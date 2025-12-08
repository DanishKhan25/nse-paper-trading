# Deployment Instructions

## Security Setup

This app is password-protected for personal use.

### Local Development
Password is stored in `.streamlit/secrets.toml` (not committed to git)
Default password: `trading123`

### Streamlit Cloud Deployment

1. **Create Private GitHub Repo**
   - Go to GitHub and create a new **PRIVATE** repository
   - Push your code:
     ```bash
     git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
     git push -u origin main
     ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Connect GitHub and select your **private** repo
   - Set main file: `app.py`
   - **IMPORTANT**: Before clicking Deploy, go to "Advanced settings"

3. **Add Password Secret**
   - In Advanced settings, add to Secrets:
     ```toml
     password = "YOUR_SECURE_PASSWORD_HERE"
     ```
   - Click "Deploy"

4. **Access Your App**
   - App URL: `https://YOUR_USERNAME-REPO_NAME.streamlit.app`
   - Enter your password to access
   - Only people with the password can use the app

## Change Password

**Locally**: Edit `.streamlit/secrets.toml`
**On Streamlit Cloud**: 
1. Go to app settings
2. Edit Secrets
3. Update password value
4. Save (app will restart)

## Additional Security

- Keep GitHub repo **PRIVATE**
- Don't share the app URL publicly
- Use a strong password
- Change password regularly
