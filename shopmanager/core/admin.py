# -*- coding: utf-8 -*-
from django.db.models import Count
from django.contrib.admin import *
from django.contrib.admin.options import *
from django.contrib import admin
from .managers import ApproxCountQuerySet
from django.utils.translation import string_concat, ugettext as _, ungettext
from django.contrib.admin.views.main import ChangeList, ORDER_VAR, SuspiciousOperation, ImproperlyConfigured, \
    IncorrectLookupParameters

NUMBER_FIELD_TYPES = (
    'AutoField',
    'BigIntegerField',
    'BinaryField',
    'DecimalField',
    'FloatField',
    'IntegerField',
    'PositiveIntegerField',
    'PositiveSmallIntegerField',
    'SmallIntegerField'
)

class BaseAdmin(admin.ModelAdmin):
    list_display = ('id',)
    search_fields = ('=id')
    date_hierarchy = None
    save_on_top = True
    readonly_fields = ()

    def save_model(self, request, obj, form, change):
        if hasattr(obj, 'creator') and not getattr(obj, 'creator'):
            obj.creator = request.user.username
        obj.save()

    def get_search_results(self, request, queryset, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        def get_field_type(field_name):
            return self.model._meta.get_field(field_name).get_internal_type()

        def is_number_type( field_name):
            field_name = field_name.lstrip('^').lstrip('=').lstrip('@')
            field_type = get_field_type(field_name)
            return field_type in NUMBER_FIELD_TYPES

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__startswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__exact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        search_fields = self.get_search_fields(request)
        if search_fields and search_term:
            orm_field_tuple = [(str(search_field), is_number_type(str(search_field)))
                               for search_field in search_fields]
            for bit in search_term.split():
                or_queries = []
                orm_lookups = []
                for field_name, is_digit in orm_field_tuple:
                    if is_digit and not bit.isdigit():
                        continue
                    field_exp = construct_search(field_name)
                    orm_lookups.append(field_exp)
                    or_queries.append(models.Q(**{field_exp: bit}))
                queryset = queryset.filter(reduce(operator.or_, or_queries))
                if not use_distinct:
                    for search_spec in orm_lookups:
                        if lookup_needs_distinct(self.opts, search_spec):
                            use_distinct = True
                            break

        return queryset, use_distinct


class ApproxAdmin(BaseAdmin):
    def queryset(self, request):
        qs = super(ApproxAdmin, self).queryset(request)
        return qs._clone(klass=ApproxCountQuerySet)


class OrderModelAdmin(BaseAdmin):

    def get_changelist(self, request, **kwargs):
        class OrderChangeList(ChangeList):
            def get_ordering(self, request, queryset):
                params = self.params
                ordering = list(self.model_admin.get_ordering(request) or self._get_default_ordering())
                if ORDER_VAR in params:
                    ordering = []
                    order_params = params[ORDER_VAR].split('.')
                    for p in order_params:
                        try:
                            none, pfx, idx = p.rpartition('-')
                            field_name = self.list_display[int(idx)]
                            order_field = self.get_ordering_field(field_name)
                            if not order_field:
                                continue
                            if order_field in OrderChangeList.orderingdict:
                                if pfx == '-':
                                    ordering.append(OrderChangeList.orderingdict[order_field][0])
                                else:
                                    ordering.append(OrderChangeList.orderingdict[order_field][1])
                            elif order_field.startswith('-') and pfx == "-":
                                ordering.append(order_field[1:])
                            else:
                                ordering.append(pfx + order_field)
                        except (IndexError, ValueError):
                            continue
                ordering.extend(queryset.query.order_by)
                pk_name = self.lookup_opts.pk.name
                if not (set(ordering) & {'pk', '-pk', pk_name, '-' + pk_name}):
                    ordering.append('-pk')
                return ordering
        OrderChangeList.orderingdict = self.orderingdict if hasattr(self, 'orderingdict') else {}
        return OrderChangeList


class BaseModelAdmin(BaseAdmin):
    @csrf_protect_m
    @transaction.atomic
    def detailform_view(self, request, object_id=None, form_url='', extra_context=None):

        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

        model = self.model
        opts = model._meta
        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)

            if not self.has_change_permission(request, obj):
                raise PermissionDenied

            if obj is None:
                raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
                    'name': force_text(opts.verbose_name), 'key': escape(object_id)})

            if request.method == 'POST' and "_saveasnew" in request.POST:
                return self.add_view(request, form_url=reverse('admin:%s_%s_add' % (
                    opts.app_label, opts.model_name),
                                                               current_app=self.admin_site.name))

        ModelForm = self.get_form(request, obj)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=not add)
            else:
                form_validated = False
                new_object = form.instance
            formsets, inline_instances = self._create_formsets(request, new_object, change=not add)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, not add)
                self.save_related(request, form, formsets, not add)
                if add:
                    self.log_addition(request, new_object)
                    return self.response_add(request, new_object)
                else:
                    change_message = self.construct_change_message(request, form, formsets)
                    self.log_change(request, new_object, change_message)
                    return self.response_change(request, new_object)
        else:
            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(request, self.model(), change=False)
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(request, obj, change=True)

        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request, obj)),
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        context = dict(self.admin_site.each_context(request),
                       title=(_('Add %s') if add else _('Change %s')) % force_text(opts.verbose_name),
                       adminform=adminForm,
                       object_id=object_id,
                       original=obj,
                       is_popup=(IS_POPUP_VAR in request.POST or
                                 IS_POPUP_VAR in request.GET),
                       to_field=to_field,
                       media=media,
                       inline_admin_formsets=inline_formsets,
                       errors=helpers.AdminErrorList(form, formsets),
                       preserved_filters=self.get_preserved_filters(request),
                       )

        context.update(extra_context or {})

        return self.render_detail_form(request, context, add=add, change=not add, obj=obj, form_url=form_url)

    def render_detail_form(self, request, context, add=False, change=False, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label
        preserved_filters = self.get_preserved_filters(request)
        form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)
        view_on_site_url = self.get_view_on_site_url(obj)
        context.update({
            'add': add,
            'change': change,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': True,  # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': view_on_site_url is not None,
            'absolute_url': view_on_site_url,
            'form_url': form_url,
            'opts': opts,
            'content_type_id': get_content_type_for_model(self.model).pk,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'to_field_var': TO_FIELD_VAR,
            'is_popup_var': IS_POPUP_VAR,
            'app_label': app_label,
        })
        if add and self.add_form_template is not None:
            form_template = self.add_form_template
        else:
            form_template = self.change_form_template

        request.current_app = self.admin_site.name

        return TemplateResponse(request, form_template or [
            "admin/%s/%s/detail_form.html" % (app_label, opts.model_name),
            "admin/%s/detail_form.html" % app_label,
            "admin/detail_form.html",
            "admin/%s/%s/change_form.html" % (app_label, opts.model_name),
            "admin/%s/change_form.html" % app_label,
            "admin/change_form.html"
        ], context)

    def get_urls(self):
        from django.conf.urls import url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            url(r'^$', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            url(r'^add/$', wrap(self.add_view), name='%s_%s_add' % info),
            url(r'^(.+)/history/$', wrap(self.history_view), name='%s_%s_history' % info),
            url(r'^(.+)/delete/$', wrap(self.delete_view), name='%s_%s_delete' % info),
            url(r'^(.+)/change/$', wrap(self.change_view), name='%s_%s_change' % info),
            url(r'^(.+)/$', wrap(self.detail_view), name='%s_%s_detail' % info),
        ]
        return urlpatterns

    def detail_view(self, request, object_id, form_url='', extra_context=None):
        return self.detailform_view(request, object_id, form_url, extra_context)