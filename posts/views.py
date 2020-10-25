from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {
        'page': page,
        'paginator': paginator,
    })


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        # Не понимаю как сделать лучше ¯\_(ツ)_/¯
        author__following__in=request.user.follower.all()
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {
        'page': page,
        'paginator': paginator,
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()  # type: ignore
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {
        'group': group,
        'page': page,
        'paginator': paginator,
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new_post.html', {
            'form': form,
        })

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(reverse('index'))


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()  # type: ignore
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = None
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    return render(request, 'profile.html', {
        'author': author,
        'page': page,
        'paginator': paginator,
        'following': following,
    })


def post_view(request, username, post_id):
    form_comment = CommentForm()
    post = get_object_or_404(Post, id=post_id, author__username=username)

    return render(request, 'post.html', {
        'author': post.author,
        'post': post,
        'form': form_comment,
    })


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post,
                             id=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'comments.html', {
            'post': post,
            'form': form,
        })
    form.instance.author = request.user
    form.instance.post = post
    form.save()
    return redirect('post_view',
                    username=post.author.username,
                    post_id=post_id)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user.username != username:
        return redirect('post_view', username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post_view', username=username, post_id=post_id)

    return render(request, 'new_post.html', {
        'form': form,
        'post': post,
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user,
                                   author=author).exists()
    if request.user != author and not follow:
        Follow.objects.create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if follow.exists():
        follow.delete()
    return redirect("profile", username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
