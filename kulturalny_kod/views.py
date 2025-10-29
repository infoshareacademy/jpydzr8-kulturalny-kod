from django.shortcuts import render, redirect


def home(request):
    if request.user.is_authenticated:
        # Redirect logged-in users to a users home page
        return redirect("users:home")
    else:
        # Show the home page to anonymous users
        return render(request, "home.html")
