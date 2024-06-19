from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from tests.factories.users import UserFactory, UserIPFactory, UserDeviceFactory
from apps.users.admin import UserIPAdmin, UserAdmin
from apps.users.models import UserDevice, UserIP

User = get_user_model()


class UserAdminTest(TestCase):
    """
    Test the UserAdmin
    """

    def setUp(self):
        """
        Create a UserAdmin instance and some User instances
        :return:
        """
        super().setUp()
        self.site = AdminSite()
        self.user_admin = UserAdmin(User, self.site)
        self.admin_user = UserFactory(
            username="admin", is_staff=True, is_superuser=True
        )

        self.client.force_login(self.admin_user)
        self.user = UserFactory(first_name="mock", last_name="user", is_active=False)
        self.user_device = UserDeviceFactory(
            user=self.user, device_identifier="device123", is_blocked=False
        )
        self.user_ip = UserIP.objects.create(
            user=self.user,
            ip_address="192.168.1.1",
            is_suspicious=False,
            is_blocked=False,
        )

    def test_block_users_and_devices_action(self):
        """
        Test the block_users_and_devices action method of the UserAdmin
        :return:
        """
        # Prepare a mock request object
        mock_request = Mock(user=self.admin_user)

        # Prepare the queryset with the user to be blocked
        queryset = User.objects.filter(username=self.user.username)

        # Directly call the action method
        self.user_admin.block_users_and_devices(mock_request, queryset)

        # Refresh data from the database
        self.user.refresh_from_db()
        device = UserDevice.objects.get(user=self.user)
        ip = UserIP.objects.get(user=self.user)

        # Check if the user is blocked
        self.assertFalse(self.user.is_active, "User should be marked as inactive")

        # Check if the user's devices are blocked
        self.assertTrue(device.is_blocked, "User's device should be marked as blocked")

        # Check if the user's IPs are marked as suspicious
        self.assertTrue(ip.is_suspicious, "User's IP should be marked as suspicious")


class UserIPAdminTest(TestCase):
    """
    Test the UserIPAdmin
    """

    def setUp(self):
        """
        Create a UserIPAdmin instance and some UserIP instances
        :return:
        """
        super().setUp()
        self.site = AdminSite()
        self.user_ip_admin = UserIPAdmin(UserIP, self.site)
        self.user1 = UserFactory(username="user1", email="user1@example.com")
        self.user2 = UserFactory(username="user2", email="user2@example.com")

        # Creating UserIP instances
        self.user_ip1 = UserIPFactory(
            user=self.user1, ip_address="192.168.1.1", region="Region1", city="City1"
        )
        self.user_ip2 = UserIPFactory(
            user=self.user2, ip_address="192.168.1.1", region="Region2", city="City2"
        )
        self.user_ip3 = UserIPFactory(
            user=self.user1, ip_address="192.168.1.2", region="Region3", city="City3"
        )

    def test_shared_user_count(self):
        """
        Test the shared_user_count method of the UserIPAdmin
        :return:
        """
        # For IP used by multiple users
        self.assertEqual(
            self.user_ip_admin.shared_user_count(self.user_ip1),
            2,
            "Should be used by 2 users",
        )

        # For IP used by a single user
        self.assertEqual(
            self.user_ip_admin.shared_user_count(self.user_ip3),
            1,
            "Should be used by 1 user",
        )

    def test_location(self):
        """
        Test the location method of the UserIPAdmin
        :return:
        """
        # Check if the location method returns the correct string
        self.assertEqual(self.user_ip_admin.location(self.user_ip1), "Region1, City1")
        self.assertEqual(self.user_ip_admin.location(self.user_ip3), "Region3, City3")

    def test_get_users_on_same_ip(self):
        """
        Test the get_users_on_same_ip method of the UserIPAdmin
        :return:
        """
        expected_users = "user2"
        self.assertEqual(
            self.user_ip_admin.get_users_on_same_ip(self.user_ip1),
            expected_users,
            "Should return user2 as another user on the same IP address",
        )

        expected_users = ""
        self.assertEqual(
            self.user_ip_admin.get_users_on_same_ip(self.user_ip3),
            expected_users,
            "Should return an empty string as there are no other users on the same IP address",
        )
