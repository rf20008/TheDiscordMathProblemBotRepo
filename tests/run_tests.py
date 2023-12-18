import unittest
import os

def discover_and_import_tests(start_dir="."):
    suite = unittest.TestSuite()

    for root, dirs, files in os.walk(start_dir):
        for file_name in files:
            if file_name.startswith("test_") and file_name.endswith(".py"):
                # Construct the module name by removing the ".py" extension
                module_name = os.path.splitext(file_name)[0]

                # Build the relative path to the module
                relative_path = os.path.relpath(os.path.join(root, file_name), start=start_dir)
                print(module_name, relative_path)
                # Import the module dynamically
                test_module = __import__(module_name, fromlist=[relative_path])

                # Iterate through the attributes of the module
                for name in dir(test_module):
                    obj = getattr(test_module, name)
                    # Check if the attribute is a class and a subclass of unittest.TestCase
                    if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                        # Add the test class to the suite
                        suite.addTest(unittest.makeSuite(obj))

    return suite

if __name__ == '__main__':
    # Run the dynamically discovered test suite
    runner = unittest.TextTestRunner()
    result = runner.run(discover_and_import_tests())
