import unittest
from unittest.mock import MagicMock

from core.container import Container


class TestContainer(unittest.TestCase):

    def setUp(self):
        """Setup mock Config and Container for each test."""
        self.mock_config = MagicMock()
        self.container = Container(self.mock_config)

    def test_register_service(self):
        """Test if service is registered correctly."""

        def mock_initializer(container):
            return "ServiceInstance"

        self.container.register('service_a', mock_initializer)

        # Check if the service is correctly added
        service = self.container._Container__services['service_a']
        self.assertIsNotNone(service)
        self.assertEqual(service.initializer, mock_initializer)
        self.assertFalse(service.initialized)

    def test_get_uninitialized_service(self):
        """Test if an uninitialized service is initialized correctly."""

        def mock_initializer(container):
            return "ServiceInstance"

        self.container.register('service_a', mock_initializer)
        service_instance = self.container.get('service_a')

        # Check if the service instance is initialized
        self.assertEqual(service_instance, "ServiceInstance")

        # Ensure the service was marked as initialized
        service = self.container.get("service_a")
        self.assertTrue(service.initialized)

    def test_get_service_that_does_not_exist(self):
        """Test if trying to fetch a non-existent service raises an error."""
        with self.assertRaises(KeyError):
            self.container.get('non_existent_service')

    def test_service_initialization_fails(self):
        """Test if the initialization failure is handled correctly."""

        def mock_initializer(container):
            raise Exception("Initialization error")

        self.container.register('service_b', mock_initializer)

        with self.assertRaises(RuntimeError):
            self.container.get('service_b')

    def test_logging_when_initializing_service(self):
        """Test if the logging correctly happens during initialization."""

        def mock_initializer(container):
            return "ServiceInstance"

        self.container.register('service_a', mock_initializer)

        with self.assertLogs(level='INFO') as log:
            self.container.get('service_a')
            self.assertIn('Initializing service: service_a', log.output)
            self.assertIn('Service service_a initialized successfully', log.output)


if __name__ == '__main__':
    unittest.main()
