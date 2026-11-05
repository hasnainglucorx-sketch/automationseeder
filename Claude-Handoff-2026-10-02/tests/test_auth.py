import unittest

from src.auth import parse_login_form


class LoginFormTests(unittest.TestCase):
    def test_parses_classic_keycloak_form(self):
        html = r'''
        <form id="kc-form-login" action="https://auth.example/submit">
          <input type="hidden" name="credentialId" value="fixture">
        </form>
        '''
        action, fields = parse_login_form(html)
        self.assertEqual(action, 'https://auth.example/submit')
        self.assertEqual(fields, {'credentialId': 'fixture'})

    def test_parses_keycloakify_context(self):
        html = r'''
        <script>const kcContext = {
          "url": {
            "loginAction": "https:\/\/keycloak.example\/login-actions\/authenticate?x=1&amp;y=2"
          }
        };</script>
        '''
        action, fields = parse_login_form(html)
        self.assertEqual(
            action,
            'https://keycloak.example/login-actions/authenticate?x=1&amp;y=2',
        )
        self.assertEqual(fields, {})


if __name__ == '__main__':
    unittest.main()
