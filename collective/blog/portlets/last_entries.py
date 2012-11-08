from zope.interface import implements

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from Products.CMFCore.utils import getToolByName

from zope import schema
from zope.formlib import form

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.blog.portlets.utils import find_assignment_context
from collective.blog.portlets import _

from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget


class ILastEntriesPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    entries = schema.Int(title=_(u"Entries"),
                         description=_(u"The number of entries to show"),
                         default=5,
                         required=True)

    root = schema.Choice(
        title=_(u"label_root_path", default=u"Root node"),
        description=_(u'help_root_path',
                      default=u"You may search for and choose a folder "
                                "to act as the root of the list. "
                                "Leave blank to use the Plone site root."),
        required=False,
        source=SearchableTextSourceBinder({'is_folderish': True},
                                          default_query='path:'))


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(ILastEntriesPortlet)

    def __init__(self, entries=5, root=None):
        self.entries = entries
        self.root = root

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return _("Last entries")


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('last_entries.pt')

    def items(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        # Get the path of where the portlet is created. That's the blog.
        assignment_context = find_assignment_context(self.data, self.context)
        folder_path = '/'.join(assignment_context.getPhysicalPath())
        # Find the blog types:
        portal_properties = getToolByName(self.context, 'portal_properties', None)
        site_properties = getattr(portal_properties, 'site_properties', None)
        portal_types = site_properties.getProperty('blog_types', None)
        if self.data.root:
            rootPath = getToolByName(self, 'portal_url').getPortalPath()
            folder_path = rootPath + self.data.root
        if portal_types == None:
            portal_types = ('Document', 'News Item', 'File')

        brains = catalog(path={'query': folder_path},
                         portal_type=portal_types,
                         sort_on='effective', sort_order='reverse')
        return brains[:self.data.entries]

    def item_url(self, item):
        portal_properties = getToolByName(self.context, 'portal_properties')
        site_properties = getattr(portal_properties, 'site_properties')
        use_view = site_properties.getProperty('typesUseViewActionInListings')
        url = item.getURL()
        if item.portal_type in use_view:
            return '%s/view' % url
        return url


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(ILastEntriesPortlet)
    form_fields['root'].custom_widget = UberSelectionWidget

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(ILastEntriesPortlet)
    form_fields['root'].custom_widget = UberSelectionWidget