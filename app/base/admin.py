from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from base.forms import CustomUserChangeForm, CustomUserCreationForm, ShiftChangeForm, ShiftCreationForm
from base.models import Role, Shift, User

# Register your models here.


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ('name', 'email', 'is_active', 'is_staff',
                    'is_superuser', 'last_login',)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'role')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active',
                                    'is_superuser')}),
        ('Dates', {'fields': ('last_login',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active', 'role')
        }
        ),
    )

    search_fields = ('email',)
    ordering = ('email',)

class ShiftAdmin(admin.ModelAdmin):
    add_form = ShiftCreationForm
    form = ShiftChangeForm
    model = Shift
    add_fieldsets = (
        (None, {'fields': ('assigned_to', 'start_at', 'end_at', 'wage_multiplier')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Role)

