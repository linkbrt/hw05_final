import os

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post


class TestPostMethods(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='test',
                                        password='test')
        self.group = Group.objects.create(title='TestGroup',
                                          slug='test',
                                          description='123')
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.data_for_reverse_func = {
            'index': '',
            'profile': {'username': self.user.username},
            'post_view': {'username': self.user.username, 'post_id': 1},
            'group_posts': {'slug': self.group.slug}
            }
        self.test_user = User.objects.create(username='test_follow',
                                             password='test')

    def test_profile_page_will_be_displayed(self):
        response = self.client.get(reverse('profile',
                                           args=[self.user.username],
                                           ),
                                   follow=True, )
        self.assertEqual(response.status_code, 200)

    def test_user_creating_post(self):
        post = self.auth_client.post(
            reverse('new_post'),
            data={'text': 'test',
                  'group': self.group.id,
                  }, follow=True
        ).context['page'][0]
        self.assertEqual(post.text, 'test',
                         msg='Something wrong with text field')
        self.assertEqual(post.author, self.user,
                         msg='Something wrong with author field')
        self.assertEqual(post.group, self.group,
                         msg='Something wrong with group field')

    def test_unlogin_user_creating_post(self):
        response = self.client.post(
            reverse('new_post'), {
                'text': 'test',
                'author': self.user
            },
            follow=True, )
        self.assertRedirects(response,
                             f"{reverse('login')}?next={reverse('new_post')}")

    def get_post_from_page(self, route_name):
        kwargs = self.data_for_reverse_func[route_name]
        response = self.client.get(reverse(route_name, kwargs=kwargs))
        if 'page' in response.context:
            return response.context['page'][0]
        else:
            return response.context['post']

    def create_test_post(self):
        return Post.objects.create(text='test',
                                   author=self.user,
                                   group=self.group)

    def test_viewing_post_on_pages(self):
        db_post = self.create_test_post()
        for route_name in self.data_for_reverse_func:
            with self.subTest(name=route_name):
                post = self.get_post_from_page(route_name)
                self.assertEqual(
                    post,
                    db_post,
                    msg=f'Запись не появилась на странице {route_name}',
                )

    def test_post_changed_correctly(self):
        post = self.create_test_post()
        self.auth_client.post(reverse('post_edit',
                                      args=[self.user.username,
                                            post.id]),
                              data={'text': 'changed_test',
                                    'group': self.group.id, })
        post = Post.objects.get(id=post.id)
        self.assertEqual(
                    'changed_test',
                    post.text,
                    msg='Запись изменилась не корректно',
                )
        self.assertEqual(
                    self.group,
                    post.group,
                    msg='Запись изменилась не корректно',
        )
        test_group = Group.objects.create(
            title='Group',
            slug='group',
            description='33333')
        post.group = test_group
        post.save()
        response = self.client.get(reverse('group_posts',
                                           args=[self.group.slug]))
        self.assertFalse(response.context['paginator'].count)

    def test_code_404_if_page_doesnt_exist(self):
        response = self.client.get('/group/')
        self.assertEqual(response.status_code, 404)

    def test_picture_is_displayed_correctly(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        _image = SimpleUploadedFile(name='test_image.gif',
                                    content=small_gif,
                                    content_type='image/gif')
        self.auth_client.post(
                reverse('new_post'), {
                    'text': 'test',
                    'author': self.user,
                    'group': self.group.id,
                    'image': _image,
                },
                follow=True, )
        for route_name in self.data_for_reverse_func:
            with self.subTest(name=route_name):
                post = self.get_post_from_page(route_name)
                self.assertEqual(post.image.name, f'posts/{_image.name}')
        os.remove(f'media/posts/{_image.name}')

    def test_triggered_protection_download_non_image_file_formats(self):
        _file = SimpleUploadedFile(name='test_image.txt',
                                   content=b'test',
                                   content_type='file/txt')
        response = self.auth_client.post(
            reverse('new_post'), {
                'text': 'test',
                'author': self.user,
                'group': self.group.id,
                'image': _file,
            },
            follow=True, )
        self.assertFormError(
            response,
            'form',
            'image',
            errors='Загрузите правильное изображение. Файл, который вы ' +
                   'загрузили, поврежден или не является изображением.')

    def test_checking_that_page_is_cached(self):
        resp1 = self.client.get(reverse('index'))
        self.create_test_post()
        resp2 = self.client.get(reverse('index'))
        self.assertHTMLEqual(str(resp1), str(resp2))

    def test_auth_user_can_follow_to_other_users(self):
        # Test auth user can follow to other users
        msg = "Auth user can't follow to other users"
        with self.subTest(msg=msg):
            self.auth_client.get(reverse('profile_follow',
                                         args=[self.test_user.username]))
            self.assertTrue(
                Follow.objects.get(user=self.user, author=self.test_user)
            )
            self.assertEqual(
                Follow.objects.all().count(),
                1,
            )

    def test_auth_user_can_unfollow_from_other_users(self):
        Follow.objects.create(user=self.user, author=self.test_user)
        # Test auth user can unfollow from other users
        msg = "Auth user can't unfollow from other users"
        with self.subTest(msg=msg):
            self.auth_client.get(reverse('profile_unfollow',
                                         args=[self.test_user.username]))
            self.assertFalse(
                Follow.objects.filter(user=self.user, author=self.test_user)
            )
            self.assertFalse(
                Follow.objects.all().exists()
            )

    def test_auth_user_can_view_posts_from_following_users(self):
        Post.objects.create(author=self.test_user,
                            text='test',
                            group=self.group)
        Follow.objects.create(user=self.user, author=self.test_user)
        # Test auth user can view posts from following users
        msg = "Auth user can't view posts from following users"
        with self.subTest(msg=msg):
            response = self.auth_client.get(reverse('follow_index'))
            post = response.context['page'][0]
            self.assertEqual(post.text, 'test',
                             msg='Something wrong with text field')
            self.assertEqual(post.author, self.test_user,
                             msg='Something wrong with author field')
            self.assertEqual(post.group, self.group,
                             msg='Something wrong with group field')

    def test_auth_user_cant_view_posts_from_unfollowing_users(self):
        Post.objects.create(author=self.test_user,
                            text='test',
                            group=self.group)
        # Test auth user can't view posts from unfollowing users
        msg = "Auth user can view posts from unfollowing users"
        with self.subTest(msg=msg):
            response = self.auth_client.get(reverse('follow_index'))
            self.assertFalse(response.context['paginator'].count)

    def test_unauth_user_cant_create_comment_(self):
        post = Post.objects.create(author=self.user,
                                   text='test',
                                   group=self.group)
        add_comment_reverse = reverse('add_comment',
                                      args=[self.user.username, post.id])
        # Test unauth user can't create comment
        msg = "Unauth user can create comment"
        with self.subTest(msg=msg):
            response = self.client.post(
                add_comment_reverse,
                data={'text': 'test'}
            )
            self.assertRedirects(
                response,
                f"{reverse('login')}?next=" +
                f"{add_comment_reverse}"
            )
            self.assertFalse(
                Comment.objects.filter(post=post,
                                       text='test',
                                       author=self.user).exists()
            )

    def test_auth_user_car_create_comment(self):
        post = Post.objects.create(author=self.user,
                                   text='test',
                                   group=self.group)
        add_comment_reverse = reverse('add_comment',
                                      args=[self.user.username, post.id])
        # Test auth user can create comment
        msg = "Auth user can't create comment"
        with self.subTest(msg=msg):
            self.auth_client.post(
                add_comment_reverse,
                data={'text': 'test'},
                follow=True
            )
            self.assertEqual(
                Comment.objects.all().count(),
                1,
            )
