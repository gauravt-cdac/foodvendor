from django.shortcuts import get_object_or_404, redirect, render
from .forms import VendorForm
from accounts.forms import UserProfileForm
from accounts.models import UserProfile
from .models import Vendor
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.views import check_role_vendor
from menu.models import Category, FoodItem
from menu.forms import CategoryForm
from django.template.defaultfilters import slugify




def get_vendor(request):
    vendor = Vendor.objects.get(user=request.user)
    return vendor

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vprofile(request):
    # Fetch UserProfile instance for logged-in user, or 404 if not found
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # Get the Vendor instance for the user, or None if not exists
    vendor = Vendor.objects.filter(user=request.user).first()

    if request.method == 'POST':
        # Bind POST data and files to forms with existing instances
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        vendor_form = VendorForm(request.POST, request.FILES, instance=vendor)

        # Validate both forms
        if profile_form.is_valid() and vendor_form.is_valid():
            # Save UserProfile form first
            profile_form.save()

            # Save Vendor form but don't commit to DB yet
            vendor_obj = vendor_form.save(commit=False)

            # Assign the current logged-in user to the vendor's user field
            vendor_obj.user = request.user
            vendor_obj.user_profile = profile  # assign user_profile explicitly
            
            # Save Vendor instance with user assigned
            vendor_obj.save()

            messages.success(request, 'Settings updated.')
            return redirect('vprofile')
        else:
            # Print form errors if validation fails (for debugging)
            print(profile_form.errors)
            print(vendor_form.errors)
    else:
        # For GET requests, instantiate forms with existing instances
        profile_form = UserProfileForm(instance=profile)
        vendor_form = VendorForm(instance=vendor)

    context = {
        'profile_form': profile_form,
        'vendor_form': vendor_form,
        'profile': profile,
        'vendor': vendor,
    }
    return render(request, 'vendor/vprofile.html', context)

# Added authentication and vendor check decorators for security
@login_required(login_url='login')  # ADDED (not present before)
@user_passes_test(check_role_vendor)  # ADDED (not present before)
def menu_builder(request):
    vendor = get_vendor(request)
    categories = Category.objects.filter(vendor=vendor).order_by('created_at')
    context = { 
        'categories': categories
    }
    return render(request, 'vendor/menu_builder.html', context)

# Corrected view: added pk as parameter to support category selection.
# Added decorators for authentication and role check
@login_required(login_url='login')  # ADDED
@user_passes_test(check_role_vendor)  # ADDED
def fooditems_by_category(request, pk):
    vendor = get_vendor(request)
    # category = get_object_or_404(Category, pk=None)  # OLD LINE
    category = get_object_or_404(Category, pk=pk)  # FIX: use pk from URL
    fooditems = FoodItem.objects.filter(vendor=vendor, category=category)
    # print(fooditems)  # OLD LINE (debug print, remove for production)
    context = {
        'fooditems': fooditems,
        'category': category,
    }
    return render(request, 'vendor/fooditems_by_category.html', context)

def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category = form.save(commit=False)
            category.vendor = get_vendor(request)
            category.slug = slugify(category_name)  
            form.save()
            messages.success(request,'Category added successfully')
            return redirect('menu_builder')
    else:
        form = CategoryForm()
    context = {
        'form' : form,
    }
    return render(request,'vendor/add_category.html',context)

def edit_category(request, pk=None):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category =  form.save(commit= False)
            category.vendor = get_vendor(request)
            category.slug = slugify(category_name)
            category.save()
            messages.success(request,'category updated successfully')
            return redirect('menu_builder')
        else:
            print(form.errors)
    else:
        form = CategoryForm(instance=category)
        context = {
            'form' : form,
            'category' : category ,
        }
    return render(request, 'vendor/edit_category.html', context)

def delete_category(request, pk=None):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, 'Category has been deleted successfully!')
    return redirect('menu_builder')