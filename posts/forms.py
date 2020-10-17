from django.forms import ModelForm, Textarea

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image', ]
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение'
        }
        help_texts = {
            'text': ' Введите текст для публикации',
            'group': 'Выберите группу для публикации',
            'image': 'Максимальный разрешенный размер файла 1MB',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]
        widgets = {
            'text': Textarea(attrs={'rows': 2}),
        }
