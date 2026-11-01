import unittest
from notion_compatibility import assess

class CompatibilityTests(unittest.TestCase):
    def test_views_are_included_in_the_detected_report(self):
        result=assess({}, {'formula':1}, [{'type':'chart'},{'type':'chart'},{'type':'map'},{'type':'table'},{'type':'future'}])
        views={x['type']:x for x in result['items'] if x['category']=='vue'}
        self.assertEqual(views['chart']['count'],2)
        self.assertEqual(views['chart']['conversion'],'unavailable')
        self.assertEqual(views['map']['conversion'],'unavailable')
        self.assertEqual(views['table']['conversion'],'adaptation')
        self.assertEqual(views['future']['conversion'],'review')
        self.assertEqual(result['items'][0]['conversion'],'snapshot')
