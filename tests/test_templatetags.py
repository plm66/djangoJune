from django import forms
from django.core.paginator import Paginator
from django.template import Context, Template
from django.test import RequestFactory

from apps.main.forms import ReportForm
from apps.main.templatetags.custom_filters import get_page_link
from tests.base import BaseTestCase
from tests.factories.main import ContentTypeFactory, ReportFactory
from tests.factories.users import UserFactory


class AddClassTemplateTagTest(BaseTestCase):
    """Test cases for the 'add_class' template tag."""

    def setUp(self) -> None:
        """Setup the initial data for the tests."""
        super().setUp()

        # Dummy form for testing
        class TestForm(forms.Form):
            """Dummy form for testing."""

            test_field = forms.CharField()

        self.form = TestForm()

    def test_add_class_template_tag(self) -> None:
        """Test the 'add_class' template tag."""
        # Load the template
        template_content = """
        {% load custom_filters %}
        {{ form.test_field|add_class:"desired-css-class" }}
        """
        template = Template(template_content)

        # Render the template
        rendered_template = template.render(Context({"form": self.form}))

        # Check if the class is added to the widget
        self.assertIn('class="desired-css-class"', rendered_template)


class ReportButtonTagTest(BaseTestCase):
    """
    Test cases for the 'report_button' template tag.
    """

    def setUp(self):
        """
        Setup the initial data for the tests.
        :return:
        """
        self.factory = RequestFactory()
        self.content_type = ContentTypeFactory.create()
        self.reporter = UserFactory.create()
        self.report = ReportFactory.create(
            content_type=self.content_type, reporter=self.reporter
        )
        self.report_form = ReportForm()

    def test_report_button_tag(self):
        """
        Test the 'report_button' template tag.
        :return:
        """
        # Create a mock request
        request = self.factory.get("/")

        # Create a template that uses the report_button tag
        template = Template(
            "{% load custom_filters %}{% report_button model_type object_id %}"
        )

        # Render the template with a context that contains the necessary data
        rendered_template = template.render(
            Context(
                {
                    "request": request,
                    "model_type": self.content_type.model,
                    "object_id": self.report.object_id,
                    "report_form": self.report_form,
                }
            )
        )

        # Assert that the rendered template contains the expected data
        self.assertIn(str(self.report.object_id), rendered_template)
        self.assertIn(self.content_type.model, rendered_template)


class PaginationTagsTest(BaseTestCase):
    """
    Test pagination template tags
    """

    def setUp(self):
        """
        Setup tests
        """
        super().setUp()
        self.factory = RequestFactory()
        self.user = UserFactory()

    def test_get_page_link(self):
        """Test the page link template tag"""
        request = self.factory.get("/some-url")
        context = Context({"request": request})

        page_link = get_page_link(context, 2)

        self.assertEqual(page_link, "/some-url?page=2")

    def test_pagination_numbers(self):
        """Test the pagination numbers template tag"""
        items = list(range(1, 101))
        paginator = Paginator(items, 10)
        page = paginator.get_page(5)
        request = self.factory.get("/some-url")
        context = Context(
            {
                "request": request,
                "page_obj": page,
            }
        )

        template = Template("{% load custom_filters %}{% pagination_numbers %}")
        output = template.render(context)

        self.assertIn("5", output)
        self.assertIn("4", output)
        self.assertIn("6", output)
        self.assertIn("1", output)
        self.assertIn("10", output)

    def test_get_query_param(self):
        """Test query params template tag"""
        request = self.factory.get("/some-url?param=value")
        context = Context({"request": request})

        template = Template(
            "{% load custom_filters %}{{ request|get_query_param:'param' }}"
        )
        output = template.render(context)

        self.assertEqual(output.strip(), "value")
