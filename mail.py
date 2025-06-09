import smtplib
from email.message import EmailMessage
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
from tkinter import font

# SMTP settings per provider
def get_smtp_settings(provider):
    provider = provider.lower()
    if provider == "gmail":
        return ("smtp.gmail.com", 465, True)
    elif provider == "outlook":
        return ("smtp.office365.com", 587, False)
    elif provider == "yahoo":
        return ("smtp.mail.yahoo.com", 465, True)
    else:
        return None

# Email sending logic with threading
def send_email():
    # Disable button and show loading
    send_button.config(state='disabled', text='Sending...', bg='#95a5a6')
    progress_bar.pack(pady=10)
    progress_bar.start(10)
    
    def email_thread():
        try:
            provider = provider_var.get()
            sender = sender_entry.get()
            password = password_entry.get()
            recipient = recipient_entry.get()
            
            # Validation
            if not all([sender, password, recipient]):
                raise ValueError("Please fill in all fields")
            
            smtp_settings = get_smtp_settings(provider)
            if smtp_settings is None:
                raise ValueError("Unsupported provider selected.")

            smtp_server, smtp_port, use_ssl = smtp_settings

            subject = "Monthly Update from Your Business"
            body = """\
Hello,

This is your monthly update. We hope you're doing well!

Please click on the following link to update Customer Information: 
https://invoiceeditor.onrender.com

Best regards,  
Your Company Name"""

            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient
            msg.set_content(body)
            
            selected_service = service_var.get()
            if selected_service:
                attachment_path = os.path.join("data", selected_service + ".xlsx")
                if os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as f:
                        file_data = f.read()
                        msg.add_attachment(file_data, maintype="application",
                                        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        filename=os.path.basename(attachment_path))


            if use_ssl:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
                    smtp.login(sender, password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.login(sender, password)
                    smtp.send_message(msg)
            
            # Success feedback
            root.after(0, lambda: success_callback(recipient))
            
        except Exception as e:
            root.after(0, lambda: error_callback(str(e)))
    
    # Start email sending in separate thread
    threading.Thread(target=email_thread, daemon=True).start()

def success_callback(recipient):
    progress_bar.stop()
    progress_bar.pack_forget()
    send_button.config(state='normal', text='✓ Email Sent!', bg='#27ae60')
    messagebox.showinfo("Success", f"Email sent successfully to {recipient}")
    root.after(2000, reset_button)

def error_callback(error_msg):
    progress_bar.stop()
    progress_bar.pack_forget()
    send_button.config(state='normal', text='❌ Failed', bg='#e74c3c')
    messagebox.showerror("Error", f"Failed to send email:\n{error_msg}")
    root.after(2000, reset_button)

def reset_button():
    send_button.config(text='Send Email', bg='#3498db')

def on_entry_focus(event):
    event.widget.config(highlightbackground='#3498db', highlightcolor='#3498db')

def on_entry_unfocus(event):
    event.widget.config(highlightbackground='#bdc3c7', highlightcolor='#bdc3c7')

# GUI Setup
root = tk.Tk()
root.title("✉️ Professional Email Sender")
root.geometry("500x650")
root.resizable(False, False)
root.configure(bg='#f8f9fa')

# Custom fonts
title_font = font.Font(family="Helvetica", size=20, weight="bold")
label_font = font.Font(family="Helvetica", size=11, weight="normal")
button_font = font.Font(family="Helvetica", size=12, weight="bold")

# Title Section
title_frame = tk.Frame(root, bg='#2c3e50', height=80)
title_frame.pack(fill='x')
title_frame.pack_propagate(False)

title_label = tk.Label(title_frame, text="📧 Email Sender", 
                      font=title_font, fg='white', bg='#2c3e50')
title_label.pack(expand=True)

# Main content frame
main_frame = tk.Frame(root, bg='#f8f9fa', padx=40, pady=30)
main_frame.pack(fill='both', expand=True)

# Provider Selection
provider_label = tk.Label(main_frame, text="📮 Email Provider", 
                         font=label_font, fg='#2c3e50', bg='#f8f9fa')
provider_label.pack(anchor='w', pady=(0, 5))

provider_var = tk.StringVar(value="Gmail")
provider_frame = tk.Frame(main_frame, bg='#f8f9fa')
provider_frame.pack(fill='x', pady=(0, 20))

style = ttk.Style()
style.theme_use('clam')
style.configure('Custom.TCombobox', 
               fieldbackground='white',
               background='#3498db',
               borderwidth=2,
               relief='solid')

provider_combo = ttk.Combobox(provider_frame, textvariable=provider_var, 
                             values=["Gmail", "Outlook", "Yahoo"],
                             style='Custom.TCombobox',
                             font=("Helvetica", 10),
                             state="readonly")
provider_combo.pack(fill='x')

# Sender Email
sender_label = tk.Label(main_frame, text="👤 Your Email Address", 
                       font=label_font, fg='#2c3e50', bg='#f8f9fa')
sender_label.pack(anchor='w', pady=(0, 5))

sender_entry = tk.Entry(main_frame, font=("Helvetica", 11), 
                       bg='white', fg='#2c3e50',
                       highlightthickness=2, highlightbackground='#bdc3c7',
                       relief='solid', bd=1)
sender_entry.pack(fill='x', ipady=8, pady=(0, 20))
sender_entry.bind("<FocusIn>", on_entry_focus)
sender_entry.bind("<FocusOut>", on_entry_unfocus)

# Password
password_label = tk.Label(main_frame, text="🔐 App Password", 
                         font=label_font, fg='#2c3e50', bg='#f8f9fa')
password_label.pack(anchor='w', pady=(0, 5))

password_entry = tk.Entry(main_frame, show='●', font=("Helvetica", 11),
                         bg='white', fg='#2c3e50',
                         highlightthickness=2, highlightbackground='#bdc3c7',
                         relief='solid', bd=1)
password_entry.pack(fill='x', ipady=8, pady=(0, 20))
password_entry.bind("<FocusIn>", on_entry_focus)
password_entry.bind("<FocusOut>", on_entry_unfocus)

# Helpful text for app password
password_help = tk.Label(main_frame, 
                        text="💡 Use app-specific password, not your regular password",
                        font=("Helvetica", 9), fg='#7f8c8d', bg='#f8f9fa')
password_help.pack(anchor='w', pady=(0, 15))

# Recipient
recipient_label = tk.Label(main_frame, text="📬 Recipient Email", 
                          font=label_font, fg='#2c3e50', bg='#f8f9fa')
recipient_label.pack(anchor='w', pady=(0, 5))

recipient_entry = tk.Entry(main_frame, font=("Helvetica", 11),
                          bg='white', fg='#2c3e50',
                          highlightthickness=2, highlightbackground='#bdc3c7',
                          relief='solid', bd=1)
recipient_entry.pack(fill='x', ipady=8, pady=(0, 30))
recipient_entry.bind("<FocusIn>", on_entry_focus)
recipient_entry.bind("<FocusOut>", on_entry_unfocus)

import os

# Scan the 'data' folder for Excel files
def get_services():
    files = os.listdir("data")
    return [f[:-5] for f in files if f.endswith(".xlsx")]

# GUI: Service Selection
service_label = tk.Label(main_frame, text="🛠 Select Service", 
                         font=label_font, fg='#2c3e50', bg='#f8f9fa')
service_label.pack(anchor='w', pady=(0, 5))

service_var = tk.StringVar()
service_combo = ttk.Combobox(main_frame, textvariable=service_var,
                             values=get_services(), font=("Helvetica", 10),
                             style='Custom.TCombobox', state="readonly")
service_combo.pack(fill='x', pady=(0, 30))


# Progress bar (initially hidden)
progress_bar = ttk.Progressbar(main_frame, mode='indeterminate', 
                              style='Custom.Horizontal.TProgressbar')

# Configure progress bar style
style.configure('Custom.Horizontal.TProgressbar',
               background='#3498db',
               troughcolor='#ecf0f1',
               borderwidth=0,
               lightcolor='#3498db',
               darkcolor='#2980b9')

# Send Button
button_frame = tk.Frame(main_frame, bg='#f8f9fa')
button_frame.pack(fill='x', pady=0)

send_button = tk.Button(button_frame, text="Send Email", 
                       command=send_email,
                       font=button_font,
                       bg='#3498db', fg='white',
                       relief='flat',
                       cursor='hand2',
                       pady=12)
send_button.pack(fill='x')

# Hover effects for button
def on_button_enter(event):
    if send_button['text'] == 'Send Email':
        send_button.config(bg='#2980b9')

def on_button_leave(event):
    if send_button['text'] == 'Send Email':
        send_button.config(bg='#3498db')

send_button.bind("<Enter>", on_button_enter)
send_button.bind("<Leave>", on_button_leave)

# Footer
footer_frame = tk.Frame(root, bg='#ecf0f1', height=40)
footer_frame.pack(fill='x', side='bottom')
footer_frame.pack_propagate(False)

footer_label = tk.Label(footer_frame, text="Made with ❤️ for professional communication", 
                       font=("Helvetica", 9), fg='#7f8c8d', bg='#ecf0f1')
footer_label.pack(expand=True)

# Center the window on screen
root.update_idletasks()
x = (root.winfo_screenwidth() // 2) - (500 // 2)
y = (root.winfo_screenheight() // 2) - (650 // 2)
root.geometry(f"500x650+{x}+{y}")

# Add some keyboard shortcuts
def on_enter_key(event):
    if send_button['state'] == 'normal':
        send_email()

root.bind('<Return>', on_enter_key)

root.mainloop()


'''vksk wrzh kdsv rvtj'''