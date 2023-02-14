from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .filters.filters import PostFilter
from .forms import PostForm
from .models import Post, Author, Category
from .utilits import is_limit_spent, DAY_POST_LIMIT


class PostsList(ListView):
    model = Post
    ordering = '-time'
    template_name = 'news.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        cat_slug = self.kwargs.get('slug')
        if ('AT' in self.request.path) or ('NW' in self.request.path):
            context = Post.objects.filter(p_type=self.kwargs['p_type'])
        elif cat_slug:
            context = Post.objects.filter(category__slug=cat_slug)
        else:
            context = Post.objects.all()
        return context

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        cat_slug = self.kwargs.get('slug')
        current_user = self.request.user
        if current_user.is_authenticated:
            context['is_limit_spent'] = is_limit_spent(current_user)

        if (Post.TP[0][0] in self.request.path) or (Post.TP[1][0] in self.request.path):
            context['quantity'] = Post.objects.filter(p_type=self.kwargs['p_type']).count()

        if Post.TP[0][0] in self.request.path:
            context['title'] = 'Статьи'
            context['post_type'] = Post.TP[0][0]
        elif Post.TP[1][0] in self.request.path:
            context['title'] = 'Новости'
            context['post_type'] = Post.TP[1][0]
        elif cat_slug:
            cat_name = Category.objects.get(slug=cat_slug)
            context['category'] = cat_name
            context['quantity'] = Post.objects.filter(category__slug=cat_slug).count()
        else:
            context['title'] = 'Все публикации'
            context['quantity'] = Post.objects.all().count()
        return context


class PostDetail(DetailView):
    model = Post
    template_name = 'new.html'
    context_object_name = 'post'


class PostSearch(ListView):
    model = Post
    ordering = '-time'
    template_name = 'search.html'
    context_object_name = 'posts'
    extra_context = {'title': 'Поиск публикации'}
    paginate_by = 4

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        if 'do_search' in self.request.GET:
            context['is_search'] = True
        return context


class PostCreate(PermissionRequiredMixin, CreateView):
    permission_required = ('news.add_post', )
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if Post.TP[0][0] in self.request.path:
            context['title'] = 'Добавить статью'
        elif Post.TP[1][0] in self.request.path:
            context['title'] = 'Добавить новость'
        return context

    def form_valid(self, form):
        if not is_limit_spent(self.request.user):
            post = form.save(commit=False)
            if Post.TP[0][0] in self.request.path:
                post.p_type = Post.TP[0][0]
            elif Post.TP[1][0] in self.request.path:
                post.p_type = Post.TP[1][0]
            author = Author.objects.get(author_acc=self.request.user)
            post.author = author
            return super().form_valid(form)
        else:
            return redirect('user_home')


class PostEdit(PermissionRequiredMixin, UpdateView):
    permission_required = ('news.change_post', )
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'
    extra_context = {'title': 'Редактировать публикацию'}


class PostDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('news.delete_post', )
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('posts_page')
    extra_context = {'title': 'Удалить публикацию'}


@login_required
def subscribe_me(request, slug):
    user = request.user
    category = Category.objects.get(slug=slug)
    categories = Category.objects.filter(subscribers__username=user)
    if category not in categories:
        category.subscribers.add(user)
    return redirect(request.META.get('HTTP_REFERER'))


def post_limit_spent_view(request):
    title = 'имя_подписчика',
    limit = DAY_POST_LIMIT
    return render(request, 'post_limit_spent.html', {'title': title, 'limit': limit})


# function for test the view of the notification email
def mail_notify_new_post_view(request):
    msg_data = {'subscriber_name': 'имя_подписчика',
        'new_post_title': 'заголовок_новой_публикации',
        'author_first_name': 'имя_автора',
        'author_last_name': 'фамилия_автора',
        'new_post_time': 'время_выхода_новой_публикации',
        'new_post_text': 'текст_новой_публикации',
        'new_post_pk': '7',
    }
    return render(request, 'notify_new_post.html', {'msg_data': msg_data, })


# function for test the view of the notification email
def mail_weekly_notify_posts_view(request):
    posts = Post.objects.filter(category__slug='politika').values('id', 'title', 'time')
    msg_data = {'subscriber_name': 'имя_подписчика', 'posts': posts}
    return render(request, 'weekly_notify_posts.html', {'msg_data': msg_data, })

