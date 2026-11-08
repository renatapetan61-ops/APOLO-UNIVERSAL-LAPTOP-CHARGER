import unittest

from amis_hardware_mapper import map_components, render_svg


class AmisHardwareMapperTests(unittest.TestCase):
    def test_maps_windows_inventory_without_inventing_physical_locations(self):
        inventory = {
            'computer': {'manufacturer': 'Example', 'model': 'Notebook'},
            'baseboard': {'manufacturer': 'Example', 'product': 'Board-A'},
            'cpu': {'name': 'CPU Model', 'cores': 4, 'logicalProcessors': 8},
            'gpus': [{'name': 'GPU Model'}],
            'memory': {'total_gb': 16},
            'disks': [{'model': 'SSD Model', 'size_gb': 512}],
            'batteries': [{'name': 'Battery', 'status': 'OK'}],
            'controllers': [{'name': 'USB Controller', 'device_id': 'PCI-VEN-0000'}],
        }
        result = map_components('Windows', inventory)
        categories = {node['category'] for node in result['nodes']}
        self.assertTrue({'motherboard', 'cpu', 'gpu', 'memory', 'storage', 'battery', 'controller'} <= categories)
        self.assertEqual(result['physical_layout'], 'NOT_DETERMINED')
        self.assertTrue(all(node['physical_location'] == 'UNKNOWN' for node in result['nodes']))

    def test_renders_svg_document(self):
        mapping = map_components('Linux', {
            'firmware_hardware': {'board_name': 'Board-X'},
            'pci_devices': ['VGA compatible controller: Example GPU'],
            'storage_devices': [{'name': 'nvme0n1', 'model': 'SSD'}],
        })
        svg = render_svg(mapping).decode('utf-8')
        self.assertTrue(svg.startswith('<svg'))
        self.assertIn('Board-X', svg)


if __name__ == '__main__':
    unittest.main()