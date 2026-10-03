from django.urls import path
from . import views

urlpatterns = [

    path(
        "generate-roadmap/",
        views.generate_roadmap,
        name="generate_roadmap"
    ),

    path(
        "my-roadmap/",
        views.my_roadmap,
        name="my_roadmap"
    ),

    path(
        "generate-roadmap-page/",
        views.generate_roadmap_page,
        name="generate_roadmap_page"
    ),
]