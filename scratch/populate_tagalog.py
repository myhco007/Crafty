import os
import sys
import django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'craftykids.settings')
django.setup()

from main.models import Flipbook

translations = {
    "handwash": (
        "Paghuhugas ng Kamay",
        "Ang paghuhugas ng kamay ay isang simpleng paraan upang mapanatiling malinis at malayo sa mikrobyo ang ating mga kamay. Ang mga bata ay dapat maghugas ng kamay gamit ang sabon at tubig upang manatiling malusog at maiwasan ang pagkakasakit. Mahalagang maghugas bago kumain, pagkatapos gumamit ng palikuran, at pagkatapos maglaro sa labas."
    ),
    "brushing teeth": (
        "Pagsipilyo ng Ngipin",
        "Ang pagsipilyo ng ngipin ay nagpapanatili ng kalinisan at kalusugan ng iyong bibig sa pamamagitan ng pag-alis ng dumi at mikrobyo. Nakatutulong ito upang maiwasan ang sirang ngipin at pinapanatiling sariwa at masigla ang iyong ngiti."
    ),
    "nail cleaning": (
        "Paglilinis ng Kuko",
        "Ang paglilinis ng kuko ay isang mahalagang bahagi ng personal na kalinisan. Nakatutulong ito na alisin ang dumi, bakterya, at mikrobyo sa ilalim at paligid ng mga kuko gamit ang mga kagamitan tulad ng gupit-kuko at kikil. Ang pagpapanatiling malinis ng mga kuko ay nakaiwas sa impeksyon at nagpapanatiling maayos ang iyong mga kamay."
    ),
    "thank you gift card": (
        "Kard ng Pasasalamat",
        "Ang Thank You Gift Card ay isang simpleng kard na ginawa upang magpakita ng pagpapahalaga. Nagtataglay ito ng malinaw na mensahe ng pasasalamat, maayos na disenyo, at espasyo para sa maikling personal na sulat. Isang munting paraan upang magpahayag ng taos-pusong pasasalamat."
    ),
    "birthday card": (
        "Kard para sa Kaarawan",
        "Ang paggawa ng birthday card ay kinabibilangan ng pagdisenyo ng makulay at masayang kard na may malinaw na bati sa kaarawan at mga palamuti. Mayroon itong espasyo para sa maikling mensahe upang maipadama ang pagmamahal sa nagdiriwang."
    ),
    "father": (
        "Kard para sa Araw ng mga Ama at Ina",
        "Ang paggawa ng kard para sa Araw ng mga Ama at Ina ay paglikha ng taos-pusong kard na may mainit na mensahe at simpleng palamuti upang ipakita ang pagmamahal at pagpapahalaga sa ating mga magulang."
    ),
    "mother": (
        "Kard para sa Araw ng mga Ama at Ina",
        "Ang paggawa ng kard para sa Araw ng mga Ama at Ina ay paglikha ng taos-pusong kard na may mainit na mensahe at simpleng palamuti upang ipakita ang pagmamahal at pagpapahalaga sa ating mga magulang."
    ),
    "diy board game": (
        "Sariling Gawang Board Game",
        "Ang DIY board game ay isang malikhaing gawain kung saan magdidisenyo at bubuo ka ng sarili mong laro, kabilang ang mga patakaran, layout ng board, at mga pyesa, na ginagawang masaya at natatangi ang paglalaro."
    ),
    "simple musical instrument": (
        "Simpleng Instrumentong Pangmusika",
        "Ang simpleng instrumentong pangmusika ay isang madaling buuing kagamitan na gumagawa ng tunog gamit ang mga pangkaraniwang kagamitan sa bahay, na nagbibigay-daan sa sinuman na lumikha ng musika sa masayang paraan."
    ),
    "animals coloring book": (
        "Aklat ng Pagkukulay ng mga Hayop at Pagtutugma ng Kulay at Hugis",
        "Ang mga gawain sa kulay at hugis ay tumutulong sa mga mag-aaral na makakilala ng iba't ibang kulay at batayang hugis, na nagpapabuti ng kanilang visual understanding at maagang kasanayan sa masayang paraan."
    ),
    "painting crafts": (
        "Mga Sining sa Pagpipinta",
        "Ang mga sining sa pagpipinta ay mga malikhaing gawain kung saan gumagamit ka ng pintura upang magpalamuti o magdisenyo ng mga bagay o likhang-sining. Tumutulong ito na maipahayag ang imahinasyon at mapahusay ang kasanayan sa sining."
    ),
    "recycled materials craft": (
        "Sining Gamit ang Recycled Materials",
        "Ang mga sining gamit ang recycled materials ay mga malikhaing proyekto na gawa sa mga ginamit muling bagay tulad ng basyong bote, karton, o lata. Nakatutulong ito sa pagbabawas ng basura habang hinihikayat ang imahinasyon."
    ),
    "paper & card board craft": (
        "Sining sa Papel at Karton - Kard na Bati",
        "Ang mga sining sa kard na bati gamit ang papel at karton ay kinabibilangan ng pagdisenyo at pagpapalamuti ng mga kard gamit ang simpleng kagamitan tulad ng makukulay na papel, karton, at kagamitang pansasining."
    ),
    "volcano models": (
        "Simpleng Eksperimento sa Siyensya - Modelong Bulkan",
        "Ang simpleng eksperimento ng modelong bulkan ay masaya at hands-on na proyekto na nagpapakita ng pagsabog ng bulkan gamit ang ligtas na kagamitan sa bahay. Ipinapakita nito ang mga batayang konseptong siyentipiko tulad ng chemical reaction habang nagbubuo ng sariling bulkan."
    ),
    "name tag": (
        "Name Tag at Sign sa Pintuan",
        "Name Tags: Maliliit na label na nagpapakita ng pangalan ng tao, pinalamutian ayon sa paksa.\n\nDisenyo sa Pintuan: Malikhaing palamuti sa pintuan upang gawin itong kaakit-akit at magiliw sa mga bisita."
    ),
    "learning goal": (
        "Layunin sa Pagkakatuto",
        "Ang Layunin sa Pagkakatuto ay isang malinaw at tiyak na pahayag na nagtatakda kung ano ang layunin ng mag-aaral na malaman, maunawaan, o magawa sa pagtatapos ng aralin o proyekto."
    ),
    "story book craft": (
        "Paggawa ng Aklat ng Kuwento",
        "Ang paggawa ng aklat ng kuwento ay ang malikhaing proseso ng pagdisenyo at pagbuo ng mga handmade na aklat o sining na may kaugnayan sa kuwento. Iniuugnay nito ang malikhaing pagsulat at pisikal na sining."
    ),
}

updated_count = 0
for flipbook in Flipbook.objects.all():
    title_lower = flipbook.title.lower()
    matched = False
    for key, (tl_title, tl_desc) in translations.items():
        if key in title_lower:
            flipbook.title_tl = tl_title
            flipbook.description_tl = tl_desc
            flipbook.save()
            print(f"Updated ID {flipbook.id}: {flipbook.title} -> {tl_title}")
            matched = True
            updated_count += 1
            break
    if not matched:
        # Fallback if title is dummy/custom
        flipbook.title_tl = flipbook.title
        flipbook.description_tl = flipbook.description
        flipbook.save()

print(f"\nSuccessfully populated Tagalog translations for {updated_count} flipbooks!")
