from django.contrib.gis.geos.point import Point
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.forms import ValidationError
from django.test import TestCase
from fixcity.bmabr.views import SRID
from fixcity.bmabr.models import RackForm
import datetime

EPOCH = datetime.datetime.utcfromtimestamp(0)

class TestCommunityBoard(TestCase):

    def test_create_cb_and_borough(self):
        from fixcity.bmabr.models import CommunityBoard, Borough
        borough = Borough(borocode=1, boroname='Staten Island')
        cb = CommunityBoard(
            gid=1,
            borocd=99, board=123, borough=borough)
        self.assertEqual(unicode(cb), u'Staten Island Community Board 123')
                            
    def test_racks_within_boundaries(self):
        from fixcity.bmabr.models import CommunityBoard, Rack
        communityboard = CommunityBoard(the_geom='MULTIPOLYGON (((0.0 0.0, 10.0 0.0, 10.0 10.0, 0.0 10.0, 0.0 0.0)))')
        rack_inside = Rack(location='POINT (5.0 5.0)', date=EPOCH)
        rack_outside = Rack(location='POINT (20.0 20.0)', date=EPOCH)
        rack_edge = Rack(location='POINT (0.0 0.0)', date=EPOCH)
        rack_inside.save()
        rack_edge.save()
        rack_outside.save()

        self.assertEqual(set(communityboard.racks),
                         set([rack_inside, rack_edge]))


class TestRack(TestCase):

    def test_create_rack(self):
        from fixcity.bmabr.models import Rack
        point = Point(1.0, 2.0, SRID)
        rack = Rack(
            address='somewhere',
            date=EPOCH,
            location=point)
        self.assertEqual(rack.verified, False)


class TestRackForm(TestCase):

    data = {'email': 'foo@bar.org',
            'verified': False,
            'title': 'A rack',
            'date': EPOCH,
            'location': Point(1.0, 2.0, SRID),
            'address': 'noplace in particular',
            }

    def test_rack_form_clean_verified__false(self):
        data = self.data.copy()
        form = RackForm(data, {})
        self.assertEqual(form.is_valid(), True)
        self.assertEqual(form.clean_verified(), False)

    def test_rack_form_clean_verified__true(self):
        data = self.data.copy()
        data['verified'] = True
        form = RackForm(data, {})
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors.get('verified'),
                         ["You can't mark a rack as verified unless it has a photo"])

    def test_rack_form_clean_photo(self):
        data = self.data.copy()
        # Jump through a few hoops to simulate a real upload.
        import os.path
        HERE = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(HERE, 'files', 'test_exif.jpg')
        content = open(path).read()
        photofile = TemporaryUploadedFile('test_exif.jpg', 'image/jpeg',
                                          len(content), None)
        photofile.write(content)
        photofile.seek(0)
        # Okay, now we have something like a file upload.
        data['photo'] = photofile
        form = RackForm(data, {'photo': photofile})
        self.assert_(form.is_valid())
        from fixcity.exif_utils import get_exif_info
        from PIL import Image
        # Make sure it doesn't have a bad rotation.        
        self.assertEqual({},
                         get_exif_info(Image.open(photofile.temporary_file_path())))
        
    
    def test_rack_form_clean(self):
        data = self.data.copy()
        form = RackForm(data, {})
        form.bound = True
        from fixcity.bmabr.models import Source
        form.instance.source = Source()
        form.is_valid()
        self.assertEqual(form.clean(), form.cleaned_data)
        form.is_bound = False
        # Unbound it still validates, we have an email in the data.
        self.assertEqual(form.clean(), form.cleaned_data)
        # But not if we don't have any of those.
        # Let's trick the form into that state...
        del(data['email'])
        form = RackForm(data, {})
        form.is_bound = False
        form.cleaned_data = data
        form._errors = {}
        self.assertRaises(ValidationError, form.clean)
        # A source is sufficient.
        form.cleaned_data['source'] = 'something'
        self.assertEqual(form.clean(), form.cleaned_data)
        

class TestSource(TestCase):

    def test_get_child_source(self):
        from fixcity.bmabr.models import TwitterSource
        ts = TwitterSource(name='twitter', user='joe', status_id='99')
        ts.save()
        from fixcity.bmabr.models import Source
        generic_source = Source.objects.filter(id=ts.id).all()[0]
        self.assertEqual(generic_source.twittersource, ts)
        self.assertEqual(generic_source.get_child_source(), ts)


class TestNYCDOTBulkOrder(TestCase):

    def test_create_and_destroy(self):
        from fixcity.bmabr.models import NYCDOTBulkOrder, User, CommunityBoard
        user = User()
        user.save()
        cb = CommunityBoard(
            the_geom='MULTIPOLYGON (((0.0 0.0, 10.0 0.0, 10.0 10.0, 0.0 10.0, 0.0 0.0)))',
            gid=1, borocd=1, board=1, borough_id=1)
        cb.save()
        bo = NYCDOTBulkOrder(user=user, communityboard=cb)
        bo.save()
        bo.delete()

    def test_racks(self):
        from fixcity.bmabr.models import NYCDOTBulkOrder, User, Rack, CommunityBoard
        user = User()
        user.save()
        cb = CommunityBoard(
            the_geom='MULTIPOLYGON (((0.0 0.0, 10.0 0.0, 10.0 10.0, 0.0 10.0, 0.0 0.0)))',
            gid=1, borocd=1, board=1, borough_id=1)
        cb.save()
        rack = Rack(location='POINT (5.0 5.0)', date=EPOCH)
        rack.save()

        bo = NYCDOTBulkOrder(user=user, communityboard=cb)

        # Initially the bulk order has no racks, even though the
        # communityboard does.
        self.assertEqual(set(cb.racks), set([rack]))
        self.assertEqual(set(bo.racks), set())

        # Saving marks all racks in the CB as locked for this bulk order.
        bo.save()
        self.assertEqual(set(bo.racks), set([rack]))
        self.assertEqual(set(bo.racks), set(cb.racks))
        # But gahhh. Django core devs think it's reasonable to chase
        # down all your references to a changed instance and reload
        # them by re-looking up the object by ID. Otherwise the state
        # in memory is out of date. (django ticket 901)
        rack = Rack.objects.get(id=rack.id)
        self.assertEqual(rack.locked, True)

        # New racks are not added to an already-saved bulk order.
        rack2 = Rack(location='POINT (7.0 7.0)', date=EPOCH)
        rack2.save()
        self.failIf(rack2 in bo.racks)
