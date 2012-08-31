from django import forms, http
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.core.mail import mail_admins
from leaves.models import Comment
from leaves.utils import get_site, get_user

class CommentForm (forms.ModelForm):
    name = forms.CharField(label='Leave this blank', required=False)

    class Meta:
        model = Comment
        fields = ('reply_to', 'author_name', 'email', 'website', 'comment')

    def __init__(self, *args, **kwargs):
        self.leaf = kwargs.pop('leaf')
        self.user = kwargs.pop('user', None)
        self.status = kwargs.pop('status', settings.LEAVES_DEFAULT_COMMENT_STATUS)
        if self.user and self.user.is_authenticated():
            kwargs['initial'] = {
                'author_name': self.user.get_full_name().strip(),
                'email': self.user.email
            }
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['reply_to'].queryset = self.leaf.comments.all()
        for field_name in self.fields:
            field = self.fields.get(field_name)
            if field and isinstance(field.widget, (forms.TextInput, forms.Textarea)):
                field.widget.attrs['placeholder'] = field.label

    def save(self, commit=True):
        obj = super(CommentForm, self).save(commit=False)
        obj.leaf = self.leaf
        obj.status = self.status
        if self.user and self.user.is_authenticated():
            obj.user = self.user
        if self.cleaned_data.get('name', '').strip():
            obj.status = 'spam'
        if commit:
            obj.save()
        return obj

def make_comment_form(leaf, data=None, site=None, user=None):
    if site is None:
        site = get_site()
    if user is None:
        user = get_user()
    status = 'published' if user and user.is_authenticated() else site.preferences.default_comment_status
    return CommentForm(data, leaf=leaf, user=user, status=status)

def comment(request, leaf):
    # If this is not a POST request, we don't do anything.
    if request.method == 'POST':
        # If the leaf does not allow comments, redirect back to the leaf as a GET, with a message.
        if not leaf.allow_comments:
            messages.error(request, 'Comments have been disabled for this %s.' % leaf.__class__.__name__.lower())
            return redirect(leaf.url)
        # We're in business. Create the comment form with the POST data, validate, and save the comment.
        comment_form = make_comment_form(leaf, request.POST, site=request.site, user=request.user)
        if comment_form.is_valid():
            comment = comment_form.save()
            messages.success(request, {
                'spam': _('Congratulations, your comment has been flagged as spam!'),
                'pending': _('Your comment has been submitted for moderation.'),
                'published': _('Your comment has been submitted.'),
            }[comment.status])
            if not settings.DEBUG and comment.status != 'spam':
                msg = '%(name)s\n%(proto)s%(domain)s%(url)s\n\n%(comment)s' % {
                    'name': comment.author_name,
                    'proto': 'https://' if request.is_secure() else 'http://',
                    'domain': request.site.domain,
                    'url': leaf.url,
                    'comment': comment.comment,
                }
                mail_admins('Comment Posted on %s' % request.site.domain, msg)
            return redirect(comment)
        else:
            messages.error(request, 'Please correct the errors below and try submitting your comment again.')
