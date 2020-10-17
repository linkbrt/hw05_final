from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, Follow, Comment


class TestPostMethods(TestCase):

    def setUp(self):

        self.user = User.objects.create(username='test',
                                        password='test')
        self.group = Group.objects.create(title='TestGroup',
                                          slug='test',
                                          description='123')
        self.client = Client()
        self.data_for_reverse_func = {
            'index': '',
            'profile': {'username': self.user.username},
            'post_view': {'username': self.user.username, 'post_id': 1},
            'group_posts': {'slug': self.group.slug}
            }

    def test_profile_page_will_be_displayed(self):

        response = self.client.get(reverse('profile',
                                           args=[self.user.username],
                                           ),
                                   follow=True, )
        self.assertEqual(response.status_code, 200)

    def test_user_creating_post(self):

        self.client.force_login(self.user)
        post = self.client.post(
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

        cache.clear()
        kwargs = self.data_for_reverse_func[route_name]
        response = self.client.get(reverse(route_name, kwargs=kwargs))
        if 'page' in response.context:
            return response.context['page'][0]
        else:
            return response.context['post']

    def create_test_post(self, image=None):

        if image:
            image = image.name
        return Post.objects.create(text='test',
                                   author=self.user,
                                   group=self.group,
                                   image=image)

    def test_viewing_post_on_pages(self):

        self.client.force_login(self.user)
        db_post = self.create_test_post()
        for route_name in self.data_for_reverse_func.keys():
            with self.subTest(name=route_name):
                post = self.get_post_from_page(route_name)
                self.assertEqual(
                    post,
                    db_post,
                    msg=f'Запись не появилась на странице {route_name}',
                )

    def test_post_changed_correctly(self):

        self.client.force_login(self.user)
        post = self.create_test_post()
        self.client.post(reverse('post_edit',
                                 args=[self.user.username,
                                       post.id]),
                         data={'text': 'changed_test',
                               'group': self.group.id, }
                         )

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

    def test_code_404_if_page_doesnt_exist(self):

        response = self.client.get('/group/')
        self.assertEqual(response.status_code, 404)

    def test_picture_is_displayed_correctly(self):

        with open('posts/image.png', 'rb') as img:
            self.create_test_post(img)
        for route_name in self.data_for_reverse_func.keys():
            with self.subTest(name=route_name):
                post = self.get_post_from_page(route_name)
                self.assertEqual(post.image, 'posts/image.png')

    def test_triggered_protection_download_non_image_file_formats(self):

        self.client.force_login(self.user)
        with open('requirements.txt', 'r') as fake_img:

            response = self.client.post(
                reverse('new_post'), {
                    'text': 'test',
                    'author': self.user,
                    'group': self.group.id,
                    'image': fake_img,
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

    def test_following_system(self):

        self.client.force_login(self.user)
        # Test auth user can follow to other users
        test_user = User.objects.create(username='test_follow',
                                        password='test')
        self.client.get(reverse('profile_follow', args=[test_user.username]))
        self.assertTrue(self.user.follower.filter(pk=1).exists())

        Post.objects.create(author=test_user,
                            text='test',
                            group=self.group)
        # Test auth user can view posts from following users
        response = self.client.get(reverse('follow_index'))
        self.assertTrue(bool(response.context['page'].object_list))
        # Test auth user can't view posts from unfollowing users
        self.client.get(reverse('profile_unfollow', args=[test_user.username]))
        self.assertFalse(self.user.follower.filter(pk=1).exists())
        # Test auth user can unfollow to other users
        response = self.client.get(reverse('follow_index'))
        self.assertFalse(bool(response.context['page'].object_list))

    def test_only_auth_user_can_create_comment_post(self):

        # Test unauth user can't create comment
        post = Post.objects.create(author=self.user,
                                   text='test',
                                   group=self.group)
        response = self.client.post(
            reverse('add_comment', kwargs={
                'username': self.user.username,
                'post_id': post.id,
            }),
            data={'text': 'test'},
            follow=True)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next=" +
            f"{reverse('add_comment', args=[self.user.username, post.id])}")
        # Test auth user can create comment
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('add_comment', kwargs={
                'username': self.user.username,
                'post_id': post.id,
            }),
            data={'text': 'test'},
            follow=True)
        self.assertEqual(response.context['comments'][0].text, 'test')
