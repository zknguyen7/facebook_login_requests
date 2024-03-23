import requests
import pyotp


class Facebook:
    def __init__(self, user, pwd, key_2fa):
        self.user = user
        self.pwd = pwd
        self.key_2fa = key_2fa
        self.session = requests.Session()

    def GetCode2Fa(self):
        otp_string = self.key_2fa
        otp_secret = ''.join(otp_string.split())
        totp = pyotp.TOTP(otp_secret)
        otp_code = totp.now()
        print(f'GET OTP 2FA: {otp_code}')
        return otp_code

    def GetCookie(self):
        url = "https://m.facebook.com/"
        payload = {}
        headers = {
            'authority': 'm.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
            'cache-control': 'max-age=0',
            'dpr': '1.25',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Snapchat/10.77.5.59 (like Safari/604.1)',
            'viewport-width': '889'
        }

        response = self.session.get(url, headers=headers, data=payload)
        fb_dtsg = response.text.split('"dtsg":{"token":"')[1].split('"')[0]
        lsd = response.text.split('"lsd":"')[1].split('"')[0]
        first_cookie = "; ".join([f"{key}={value}" for key, value in response.cookies.get_dict().items()])
        #print(f'fb_dtsg: {fb_dtsg}\nlsd: {lsd}\nfirst_cookie: {first_cookie}')
        return first_cookie, fb_dtsg, lsd
    
    def LoginUserPass(self, fb_dtsg, lsd):
        url = "https://m.facebook.com/login/device-based/regular/login/?refsrc=deprecated&lwv=100"
        payload = {
            'lsd': lsd,
            'jazoest': '2850',
            'm_ts': '1692843730',
            'try_number': '0',
            'fb_dtsg': fb_dtsg,
            'unrecognized_tries': '0',
            'email': self.user,
            'pass': self.pwd,
            'login': 'Đăng nhập',
            'bi_xrwh': '0'
        }
        response = self.session.post(url, data=payload)
        if 'Số di động hoặc email bạn nhập không khớp với bất kỳ tài khoản nào' in response.text:
            print(f'[ {self.user}|{self.pwd}|Email or password invalid ]')
            return 'user|pass|invalid'
        fb_dtsg = response.text.split('name="fb_dtsg" value="')[1].split('"')[0]
        nh = response.text.split('name="nh" value="')[1].split('"')[0]
        return fb_dtsg, nh

    def Submit2Fa(self, fb_dtsg, nh):
        url = "https://m.facebook.com/login/checkpoint/"
        payload = {
            'fb_dtsg' : fb_dtsg,
            'jazoest': '2866',
            'checkpoint_data': '',
            'approvals_code': self.GetCode2Fa(),
            'codes_submitted': '0',
            'submit[Submit Code]': 'Gửi mã',
            'nh': nh
        }

        response = self.session.post(url, data=payload)
        fb_dtsg = response.text.split('name="fb_dtsg" value="')[1].split('"')[0]
        nh = response.text.split('name="nh" value="')[1].split('"')[0]
        return fb_dtsg, nh

    def RememberBrowser(self, fb_dtsg, nh):
        url = "https://m.facebook.com/login/checkpoint/"
        payload = {
            'fb_dtsg': fb_dtsg,
            'jazoest': '21069',
            'checkpoint_data': '',
            'name_action_selected': 'save_device',
            'submit[Continue]': 'Tiếp tục',
            'nh': nh
        }
        response = self.session.post(url, data=payload)
        if 'name="submit[Continue]"' in response.text:
            fb_dtsg = response.text.split('name="fb_dtsg" value="')[1].split('"')[0]
            nh = response.text.split('name="nh" value="')[1].split('"')[0]
            return self.ReviewRecentLogin(fb_dtsg, nh)
        elif 'tài khoản của bạn đã bị khóa' in response.text:
            print(f'[ {self.user}|{self.pwd}|Lock 956 ]')
            return '956'
        return self.session.cookies.get_dict()
    
    def ReviewRecentLogin(self, fb_dtsg, nh):
        url = "https://m.facebook.com/login/checkpoint/"
        payload = {
            'fb_dtsg': fb_dtsg,
            'jazoest': '2972',
            'checkpoint_data': '',
            'submit[Continue]': 'Continue',
            'nh': nh
        }
        response = self.session.post(url, data=payload)
        fb_dtsg = response.text.split('name="fb_dtsg" value="')[1].split('"')[0]
        nh = response.text.split('name="nh" value="')[1].split('"')[0]
        url = "https://m.facebook.com/login/checkpoint/"
        payload = {
            'fb_dtsg': fb_dtsg,
           'jazoest': '21022',
           'checkpoint_data': '',
           'submit[This was me]': 'Đây là tôi',
           'nh': nh
        }
        response = self.session.post(url, data=payload)
        fb_dtsg = response.text.split('name="fb_dtsg" value="')[1].split('"')[0]
        nh = response.text.split('name="nh" value="')[1].split('"')[0]
        url = "https://m.facebook.com/login/checkpoint/"
        payload = {
            'fb_dtsg': fb_dtsg,
            'jazoest': '21069',
            'checkpoint_data': '',
            'name_action_selected': 'save_device',
            'submit[Continue]': 'Tiếp tục',
            'nh': nh
        }
        response = self.session.post(url, data=payload)
        return self.session.cookies.get_dict()
        
    def Main(self):
        first_cookie, fb_dtsg, lsd = self.GetCookie()
        result = self.LoginUserPass(fb_dtsg, lsd)
        if result != 'user|pass|invalid':
            fb_dtsg, nh = self.Submit2Fa(result[0], result[1])
            cookie = self.RememberBrowser(fb_dtsg, nh)
            if cookie != '956':
                cookie = "; ".join([f"{key}={value}" for key, value in cookie.items()])
                print(f'[{cookie}]')

if __name__ == "__main__":
    user = ""
    pwd = ""
    key_2fa = ""
    facebook_instance = Facebook(user, pwd, key_2fa)  
    facebook_instance.Main()

