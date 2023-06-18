from django.contrib import admin
from .models import Post

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'content',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Post, PostAdmin)