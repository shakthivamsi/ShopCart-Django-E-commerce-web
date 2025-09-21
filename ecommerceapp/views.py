from django.shortcuts import render, redirect
from django.contrib import messages
from ecommerceapp.models import Contact, Product, OrderUpdate, Orders
from django.conf import settings
from math import ceil
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
from django.shortcuts import get_object_or_404


@csrf_exempt
def payment_status(request):
    if request.method == "POST":
        data = request.POST

        if data.get("razorpay_payment_id"):
            try:
                order = Orders.objects.get(oid=data.get("razorpay_order_id"))
                order.amountpaid = order.amount  # store full paid amount
                order.paymentstatus = "SUCCESS"
                order.save()
            except Orders.DoesNotExist:
                messages.warning(request, "Order not found in database.")

            messages.success(request, "Payment Successful!")
            return render(request, "paymentstatus.html", {
                "response": {
                    "RESPCODE": "01",
                    "ORDERID": data.get("razorpay_order_id")
                }
            })

        else:
            try:
                order = Orders.objects.get(oid=data.get("razorpay_order_id"))
                order.paymentstatus = "FAILED"
                order.save()
            except Orders.DoesNotExist:
                pass  # no action needed if order not found

            messages.error(request, "Payment Failed!")
            return render(request, "paymentstatus.html", {
                "response": {
                    "RESPCODE": "00",
                    "ORDERID": data.get("razorpay_order_id")
                }
            })

    return redirect("/")

def index(request):
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    return render(request, "index.html", {'allProds': allProds})


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        desc = request.POST.get("desc")
        pnumber = request.POST.get("pnumber")

        # Save contact message to DB
        Contact.objects.create(name=name, email=email, desc=desc, phonenumber=pnumber)

        # Email to Admin
        subject = f"New Contact Form Submission from {name}"
        message = f"""
You have a new contact request:

Name: {name}
Email: {email}
Phone: {pnumber}

Message:
{desc}
"""
        send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])

        # Auto-reply to User
        reply_subject = "We Received Your Message"
        reply_message = f"Hi {name},\n\nThank you for contacting us. We'll get back to you shortly.\n\n- ShopyCart Team"
        send_mail(reply_subject, reply_message, settings.EMAIL_HOST_USER, [email])

        messages.info(request, "Thank you for contacting us.We received your message and sent a confirmation email.")
        return redirect('/contact')

    return render(request, "contact.html")

def about(request):
    return render(request, "about.html")


def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login & Try Again")
        return redirect('/auth/login')

    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amt')
        email = request.POST.get('email', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')

        # ✅ Validate amount
        if not amount or not amount.isdigit() or int(amount) < 1:
            messages.error(request, "Invalid amount. Please check your cart.")
            return redirect('/checkout/')

        amount = int(amount)

        # ✅ Create order in DB
        order = Orders.objects.create(
            items_json=items_json,
            name=name,
            amount=amount,
            email=email,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone
        )

        OrderUpdate.objects.create(order_id=order.order_id, update_desc="The order has been placed.")

        # ✅ Razorpay Integration
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment = client.order.create({
            "amount": amount * 100,  # Razorpay expects amount in paise
            "currency": "INR",
            "payment_capture": 1
        })

        order.oid = payment['id']
        order.save()

        context = {
            'payment': payment,
            'order': order,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        }
        return render(request, 'razorpay_checkout.html', context)

    # ✅ For GET request (when user visits the page)
    return render(request, "checkout.html")


# def profile(request):
#     if not request.user.is_authenticated:
#         messages.warning(request, "Login & Try Again")
#         return redirect('/auth/login')

#     currentuser = request.user.username
#     items = Orders.objects.filter(email=currentuser)

#     # Attach latest update to each order
#     for order in items:
#         latest_update = OrderUpdate.objects.filter(order_id=order.order_id).order_by('-timestamp').first()
#         order.latest_update = latest_update


#     return render(request, "profile.html", {
#         "items": items,
#     })



def profile(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login & Try Again")
        return redirect('/auth/login')

    currentuser = request.user.email
    items = Orders.objects.filter(email=currentuser)

    for order in items:
        # Parse product list from JSON
        order.products = []
        try:
            parsed = json.loads(order.items_json)
            for key, val in parsed.items():
                qty = val[0]
                pname = val[1]
                price = val[2]
                order.products.append(f"{qty} x {pname} (₹{price})")
        except:
            order.products.append("Error parsing products")

        # Attach latest order update
        order.latest_update = OrderUpdate.objects.filter(order_id=order.order_id).order_by('-timestamp').first()
        # ✅ Add fallback for 'delivered'
        order.is_delivered = getattr(order.latest_update, 'delivered', False)


    return render(request, "profile.html", {
        "items": items
    })



def invoice(request, oid):
    order = get_object_or_404(Orders, order_id=oid)
    order.latest_update = OrderUpdate.objects.filter(order_id=oid).order_by('-timestamp').first()

    # parse items_json
    try:
        parsed = json.loads(order.items_json)
        order.products = []
        for key, val in parsed.items():
            qty = int(val[0])
            name = val[1]
            price = int(val[2])
            total = qty * price
            order.products.append({
                "name": name,
                "qty": qty,
                "price": price,
                "total": total,
            })
    except:
        order.products = []

    return render(request, "invoice.html", {"order": order})

