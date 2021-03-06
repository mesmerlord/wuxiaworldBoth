from django.db.models.signals import post_delete, pre_save,post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.utils.text import slugify
from django_celery_beat.models import IntervalSchedule, PeriodicTask
import json
from wuxiaworld.scraper.tasks import continous_scrape
from django.utils.timezone import now
from django.db.models import Avg
from django.core.cache import cache
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
#If Novel has a scrape link, start the initial scrape of the novel and create
# a periodic task to scrape every x interval.
from allauth.account.signals import user_signed_up

def create_periodic_task(instance):
    if instance.repeatScrape:
        schedule, _ = IntervalSchedule.objects.get_or_create(
                    every = 12,
                    period = IntervalSchedule.HOURS
                    )
        task, _ = PeriodicTask.objects.get_or_create(
        interval=schedule, 
        name=instance.name,
        task='wuxiaworld.scraper.tasks.continous_scrape',
        args = json.dumps([instance.slug]),
        )

@receiver(post_delete, sender="novels.Profile")
def delete_settings(sender, instance, **kwargs):
    settings = instance.settings
    if settings:
        settings.delete()
     
@receiver(post_delete, sender="novels.Novel")
def clear_views(sender,instance, **kwargs):
    novelView = instance.views
    if novelView:
        novelView.delete()
    novelTask = PeriodicTask.objects.filter(name = instance.name)
    if novelTask:
        novelTask.delete()

@receiver(post_save, sender="novels.Chapter")
def update_novel_last_chapter(sender, instance, created, **kwargs):
    if created:
        novel_obj = instance.novelParent
        novel_obj.last_chap_updated = now()
        novel_obj.save()

@receiver(post_save, sender="novels.Review")
def update_novel_review_rating(sender, instance, created, **kwargs):
    Review = apps.get_model("novels", "Review")
    novel_obj = instance.novel

    all_reviews = Review.objects.filter(novel = novel_obj)
    if all_reviews.count():
        avg_rating = all_reviews.aggregate(score = Avg('total_score'))
        novel_obj.rating = round(avg_rating['score'], 2)
        novel_obj.save()

@receiver(pre_save,sender = "novels.Novel")
def novel_check(sender,instance,**kwargs):
    
    if not instance.slug:
        newSlug = slugify(instance.name)
        instance.slug = newSlug
    if not instance.views:
        NovelViews = apps.get_model('novels','NovelViews')
        novelView, _ = NovelViews.objects.get_or_create(viewsNovelName = instance.slug)
        instance.views = novelView

    if not instance.category:
        Category = apps.get_model('novels','Category')
        noneCategory, _ = Category.objects.get_or_create(name = "None", slug = "none")
        instance.category = noneCategory

    
@receiver(post_save,sender = "novels.Novel")
def init_scrape(sender,instance,**kwargs):
    if kwargs['created']:
        create_periodic_task(instance)

@receiver(user_signed_up)
def create_profile(sociallogin, user, **kwargs):

    if sociallogin.account.provider == 'facebook':
        user_data = user.socialaccount_set.filter(provider='facebook').first()
        imageUrl = user_data.get_avatar_url()          

    if sociallogin.account.provider == 'google':
        user_data = user.socialaccount_set.filter(provider='google').first()
        imageUrl = user_data.get_avatar_url()          

    Profile = apps.get_model('novels','Profile')
    Settings = apps.get_model('novels','Settings')
    newSettings = Settings.objects.create()
    profile = Profile.objects.create(user=user, imageUrl = imageUrl,
                        settings = newSettings)

@receiver(post_save, sender="novels.Settings")
def settings_cache(sender, instance, created, **kwargs):
    if not created and instance.profile:
        cache.set(f"profile_{instance.profile.user.id}", instance.updated_at)