from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # 1. READ: Fields to display in the list view
    list_display = ('name', 'student_id', 'has_encoding')
    
    # 2. SEARCH: Add a search bar for name or ID
    search_fields = ('name', 'student_id')
    
    # 3. FILTER: Add a filter sidebar
    list_filter = ('name',)

    # Custom column to show if encoding exists (Data Analyst touch)
    def has_encoding(self, obj):
        return bool(obj.encoding)
    has_encoding.boolean = True # Shows a nice Green Check/Red Cross
    has_encoding.short_description = 'Face Captured?'