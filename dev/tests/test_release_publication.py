import io
import os
from pathlib import Path
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import patch
from tools import publish_release as publisher

class PublicationTests(unittest.TestCase):
    def test_assets_are_uploaded_before_the_release_is_published(self):
        with tempfile.TemporaryDirectory() as folder:
            artifact=Path(folder)/'Any2Any-0.10.0.zip';artifact.write_bytes(b'zip!');checksum=artifact.with_suffix('.sha256');checksum.write_bytes(b'checksum')
            sha='a'*40;calls=[]
            def request(url,token,body=None,**kw):
                calls.append((url,body,kw.get('method','GET')))
                if '/releases/tags/' in url:raise urllib.error.HTTPError(url,404,'missing',{},None)
                if url.endswith('/releases'):
                    self.assertTrue(body['draft']);self.assertEqual(body['target_commitish'],sha)
                    return {'id':1,'draft':True,'target_commitish':sha,'upload_url':'https://uploads.github.com/repos/owner/repo/releases/1/assets{?name,label}','assets':[]}
                if url.startswith('https://uploads.github.com'):return {'size':len(body)}
                self.assertEqual(calls[-1][2],'PATCH');self.assertFalse(body['draft']);return {'html_url':'https://github.com/owner/repo/releases/tag/v0.10.0'}
            with patch.dict(os.environ,{'GITHUB_REPOSITORY':'owner/repo','GITHUB_SHA':sha,'GH_TOKEN':'fake-test-token'}),patch.object(publisher,'build',return_value=(artifact,1,'hash')),patch.object(publisher,'request',side_effect=request),redirect_stdout(io.StringIO()) as output:
                publisher.publish()
            self.assertEqual([c[2] for c in calls],['GET','POST','POST','POST','PATCH']);self.assertNotIn('fake-test-token',output.getvalue())

    def test_missing_windows_bundle_blocks_publication_before_any_github_write(self):
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'owner/repo','GITHUB_SHA':'a'*40,'GH_TOKEN':'fake'}),patch.object(publisher,'build',return_value=(Path('unused'),1,'hash')),patch.object(publisher,'request') as request:
            with self.assertRaisesRegex(ValueError,'Windows archive'):publisher.publish(require_windows=True)
        request.assert_not_called()

    def test_existing_public_release_is_never_overwritten(self):
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'owner/repo','GITHUB_SHA':'a'*40,'GH_TOKEN':'fake'}),patch.object(publisher,'build',return_value=(Path('unused'),1,'hash')),patch.object(publisher,'request',return_value={'draft':False}) as request:
            with self.assertRaisesRegex(ValueError,'already published'):publisher.publish()
        request.assert_called_once()

    def test_credential_is_not_sent_to_an_unexpected_upload_host(self):
        with self.assertRaisesRegex(ValueError,'Unexpected GitHub API host'):publisher.request('https://example.org/upload','fake-token',b'file',method='POST')

if __name__=='__main__':unittest.main()
