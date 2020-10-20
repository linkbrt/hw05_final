from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image', ]
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение'
        }
        help_texts = {
            'text': 'Текст записи:',
            'group': 'Выберите группу для публикации:',
            'image': 'Загрузите изображение:',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5, 'id': "FormControlText",
                'placeholder': 'Введите текст для публикации'}
            ),
            'group': forms.Select(attrs={
                'class': 'form-control',
                'id': "FormControlGroup"}
            ),
            'image': forms.FileInput(attrs={
                'class': 'custom-file-input',
                'id': "customFile"}
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }
