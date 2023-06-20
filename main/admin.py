from django.contrib import admin
from .models import Post, PostVote
from django import forms

class PostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Post
        fields = '__all__'

class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'content',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Post, PostAdmin)

class PostVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'votes', 'timestamp')
    search_fields = ('user__username', 'post__title')

    def votes(self, obj):
        return obj.post.votes
    votes.short_description = 'Votes'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('post')
        return queryset

admin.site.register(PostVote, PostVoteAdmin)