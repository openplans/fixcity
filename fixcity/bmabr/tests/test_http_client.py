# XXX I feel kinda icky importing settings during test

from django.test import TestCase

from fixcity.bmabr.management.commands.utils import FixcityHttp
from fixcity.bmabr.management.commands.utils import SERVER_TEMP_FAILURE, SERVER_ERROR

import mock
import os

HERE = os.path.abspath(os.path.dirname(__file__))


class StubErrorAdapter:

    general_error_message = "General Error"

    def validation_errors(self, errordict):
        """Convert the form field names in the errors dict into things
        that are meaningful via the twitter workflow, and adjust error
        messages appropriately too.
        """
        return "Validation error"

    server_error_retry = "Server Error Retry"

    server_error_permanent = "Server Error Permanent"


class TestFixcityHttp(TestCase):

    @mock.patch('httplib2.Response')
    @mock.patch('httplib2.Http.request')
    @mock.patch('logging.Logger.debug')
    @mock.patch('fixcity.bmabr.management.commands.handle_mailin.Notifier')
    def test_do_post__success(self, mock_notifier, mock_debug,  mock_request,
                              mock_response):
        response = mock_response()
        notifier = mock_notifier()
        response.status = 200
        mock_request.return_value = (response, 'hello POST world')
        http = FixcityHttp(mock_notifier(), StubErrorAdapter())
        status, content = http.do_post('http://example.com', 'test body')
        self.assertEqual(content, 'hello POST world')
        self.assertEqual(status, 200)
        self.failIf(notifier.bounce.call_count)


    @mock.patch('httplib2.Response')
    @mock.patch('httplib2.Http.request')
    @mock.patch('logging.Logger.debug')
    @mock.patch('fixcity.bmabr.management.commands.handle_mailin.Notifier')
    def test_do_post__500_error(self, mock_notifier, mock_debug,  mock_request,
                                mock_response):
        response = mock_response()
        notifier = mock_notifier()
        response.status = 500
        mock_request.return_value = (response, 'hello POST world')
        http = FixcityHttp(notifier, StubErrorAdapter())

        status, content = http.do_post('http://example.com', 'test body')
        self.assertEqual(status, 500)
        self.assertEqual(content, 'hello POST world')
        self.assertEqual(notifier.bounce.call_count, 1)
        bounce_kwargs = notifier.bounce.call_args[-1]
        self.assertEqual(bounce_kwargs, {'notify_admin_body': 'hello POST world',
                                         'notify_admin': '500 Server error'})



    @mock.patch('httplib2.Http.request')
    @mock.patch('logging.Logger.debug')
    @mock.patch('fixcity.bmabr.management.commands.handle_mailin.Notifier')
    def test_do_post__socket_error(self, mock_notifier, mock_debug,
                                   mock_request):
        import socket
        notifier = mock_notifier()
        mock_request.side_effect = socket.error("kaboom")
        http = FixcityHttp(notifier, StubErrorAdapter())
        status, content = http.do_post('http://example.com', 'test body')
        self.assertEqual(status, None)
        self.assertEqual(content, None)
        self.assertEqual(notifier.bounce.call_count, 1)
        bounce_kwargs = notifier.bounce.call_args[-1]
        self.assertEqual(bounce_kwargs, {'notify_admin': 'Server down??'})


    @mock.patch('httplib2.Response')
    @mock.patch('httplib2.Http.request')
    @mock.patch('logging.Logger.debug')
    @mock.patch('fixcity.bmabr.management.commands.handle_mailin.Notifier')
    def test_do_post_json(self, mock_notifier, mock_debug, mock_request,
                          mock_response):
        response = mock_response()
        notifier = mock_notifier()
        response.status = 200
        mock_request.return_value = (response, '{"foo": "bar"}')
        http = FixcityHttp(notifier, StubErrorAdapter())

        content = http.do_post_json('http://example.com',
                                    "{'some key': 'some value'}")
        self.assertEqual(content, {'foo': 'bar'})
        self.failIf(notifier.bounce.call_count)


    @mock.patch('httplib2.Response')
    @mock.patch('httplib2.Http.request')
    @mock.patch('logging.Logger.debug')
    @mock.patch('fixcity.bmabr.management.commands.handle_mailin.Notifier')
    def test_do_post_json__validation_errors(self, mock_notifier, mock_debug,
                                             mock_request, mock_response):
        response = mock_response()
        notifier = mock_notifier()
        response.status = 200
        from django.utils import simplejson as json
        error_body = json.dumps(
            {'errors': {'title': ['This field is required.']}})
        mock_request.return_value = (response, error_body)
        http = FixcityHttp(notifier, StubErrorAdapter())

        content = http.do_post_json('http://example.com',
                                     "{'some key': 'some value'}")
        self.assertEqual(content, json.loads(error_body))
        self.assertEqual(notifier.bounce.call_count, 1)


    @mock.patch('httplib2.Response')
    @mock.patch('httplib2.Http.request')
    @mock.patch('logging.Logger.debug')
    @mock.patch('fixcity.bmabr.management.commands.handle_mailin.Notifier')
    def test_submit__successful_empty_result(self, mock_notifier, mock_debug,
                                             mock_request, mock_response):
        response = mock_response()
        notifier = mock_notifier()
        response.status = 200
        mock_request.return_value = (response, '{}')
        http = FixcityHttp(notifier, StubErrorAdapter())
        self.assertEqual(http.submit({}), None)
        self.assertEqual(notifier.on_submit_success.call_count, 0)


    @mock.patch('fixcity.bmabr.management.commands.tweeter.Notifier')
    @mock.patch('httplib2.Response')
    @mock.patch('httplib2.Http.request')
    @mock.patch('logging.Logger.debug')
    def test_submit__network_error(self, mock_debug,
                                   mock_request, mock_response, mock_notifier):
        mock_response.status = 500
        mock_request.return_value = (mock_response, 'blah')
        http = FixcityHttp(mock_notifier, StubErrorAdapter())
        data = {}
        http.submit(data)
        self.assertEqual(mock_notifier.bounce.call_count, 1)
        kwargs = mock_notifier.bounce.call_args[1]
        self.assertEqual(kwargs,
                         {'notify_admin_body': 'blah',
                          'notify_admin': '500 Server error'})


    @mock.patch('httplib2.Response')
    @mock.patch('fixcity.bmabr.management.commands.utils.FixcityHttp.do_post')
    @mock.patch('logging.Logger.debug')
    @mock.patch('fixcity.bmabr.management.commands.handle_mailin.Notifier')
    def test_submit__with_photos_and_user(self, mock_notifier, mock_debug,
                                          mock_do_post,
                                          mock_response):
        # XXX Most of this functionality is now in utils. MOve test 
        # somewhere more appropriate.

        # Mock typically uses side_effect() to specify multiple return
        # value; clunky API but works fine.
        do_post_return_values = [
            (200, '''{
            "user": "bob",
            "photo_post_url": "/photos/",
            "rack_url": "/racks/1"
            }'''),
            (200, 'OK')]
        def side_effect(*args, **kw):
            return do_post_return_values.pop(0)
        mock_do_post.side_effect = side_effect
        notifier = mock_notifier()
        http = FixcityHttp(notifier, StubErrorAdapter())

        # Mock photo needs to be just file-like enough.
        mock_photo_file = mock.Mock()
        mock_photo_file.name = 'foo.jpg'
        mock_photo_file.fileno.side_effect = AttributeError()
        mock_photo_file.tell.return_value = 12345
        mock_photo_file.read.return_value = ''

        self.assertEqual(http.submit({'photos': {'photo': mock_photo_file}}),
                         None)
        self.assertEqual(notifier.on_submit_success.call_count, 1)
        vars = notifier.on_submit_success.call_args[0][0]
        self.assert_(vars.has_key('rack_url'))
        self.assert_(vars.has_key('rack_user'))

    @mock.patch('fixcity.bmabr.management.commands.tweeter.Notifier')
    @mock.patch('fixcity.bmabr.management.commands.tweeter.shorten_url')
    @mock.patch('logging.Logger.info')
    @mock.patch('fixcity.bmabr.management.commands.utils.FixcityHttp.do_post')
    def test_submit__user_errors(self, mock_do_post, mock_info,
                                 mock_shorten, mock_notifier):
        http = FixcityHttp(mock_notifier, StubErrorAdapter())
        mock_do_post.return_value = (200, '{"errors": {"any": "thing at all"}}')
        mock_shorten.return_value = 'http://short_url/'

        http.submit({'title': 'TITLE', 'address': 'ADDRESS',
                     'twitter_user': 'USER', 'date':  'DATE',
                     'twitter_id': 123})
        self.assertEqual(mock_do_post.call_count, 1)
        # We notified the user of failure.
        self.assertEqual(mock_notifier.bounce.call_count, 1)
        notify_args, notify_kwargs = mock_notifier.bounce.call_args
        self.assertEqual(notify_args[1], 'Validation error')
