from main.models import User
users = User.objects.filter(profile__role='CLIENT', profile__is_approved=False)
count = users.count()
for u in users:
    u.profile.is_approved = True
    u.profile.save()
print(f'Approved {count} client accounts.')
