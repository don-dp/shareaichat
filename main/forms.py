from django import forms
from .models import Comment, Post

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'extra_info']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
            'extra_info': forms.Textarea(attrs={'rows': 3, 'placeholder': 'optional. You can include model info or the service such as google bard or chatgpt.'}),
        }