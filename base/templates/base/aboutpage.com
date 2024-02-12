{% extends "base/base.html" %}

{% block title %}About | Share AI Chat{% endblock %}

{% block content %}
<ul>
    <li>Share AI Chat allows you to share conversations from locally running LLMs such as Mistral and LLaMA.</li>
    <li>You can comment on the shared conversations, like a forum.</li>
    <li>The home page has a list of posts by users which you can sort by popularity or new.</li>
    <li>Contact: hello@mydomain.com</li>
</ul>

<p><b>How This Website Works:</b></p>
<ol>
    <li><b>Creating Posts:</b> Direct creation of posts on this platform is fully supported, allowing for seamless sharing of conversations. Users can easily copy their conversations from their CLI or chat interface and paste them directly into the platform. This method offers a straightforward way to share insights and discussions without the need for additional tools.</li>
    <li><b>Editing Posts:</b> not supported.</li>
    <li><b>Editing Titles:</b> You may edit the title of your post to best reflect its content.</li>
    <li><b>Commenting:</b> Commenting is supported for posts. Root level comments are sorted by votes, and one level of replies are supported and ordered chronologically, similar to YouTube comments.</li>
    <li><b>Editing and Deleting Comments:</b> Editing comments is supported. However, deleting comments is not supported.</li>
    <li><b>Voting:</b> Voting is supported on posts and comments.</li>
    <li><b>Deleting Posts:</b> Deleting is supported for 1 hour after creating a post. If your chat includes sensitive information or you've changed your mind about sharing the chat, you can delete your post within this window. If you to delete your posts beyond this window, please contact me via email which is displayed above.</li>
    <li><b>Profile Updates:</b> You can change your email address in the profile page.</li>
</ol>

{% endblock %}