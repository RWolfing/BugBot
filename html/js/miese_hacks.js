const review = [
    "Entweder ist die Bildqualität sehr bescheiden, der stream bricht relativ häufig ab oder die Tonspur ist versetzt. Am Internet kann es nicht liegen, da andere Mediatheken ohne Probleme laufen.",
    "Der Ton um mehrere Sekunden versetzt zum Bild, App stürzt alle 20 Minuten ab und das Bild ist einfach miserabel!",
    "LiveTV geht nicht",
    "Funktioniert nicht!",
    "Schlecht",
    "Videos werden gar nicht abgespielt auch nicht wenn man sie vorher runterläd. Somit unbrauchbar für mich.",
    "Ich will die App vor allem mittels Chromecast am Fernseher nutzen. Leider kommt es dabei haufig zu Abbrüchen und Zwangspausen (häufig alle 2-3 Sekunden). Ich habe die diversen Fehlerquellen hinterfragt (ZDF App, Smartphone, Router, Internetverbindung, Chromecast-Stick), bin aber der Meinung es muss an der ZDF App liegen.",
    "Alle Videos ruckeln leider alle 10 - 15 Sekunden einmal kurz. Ich benutze einen neuen Sony bravia mit Android Software und immer tritt dieser Fehler auf. Ich habe auch schon Die App zurückgesetzt und neu installiert. Bei meinem alten Samsung TV mit eigener Samsung App laufen die Videos Flüssig durch.",
]

const user = [
    "Android User",
    "iOS User"
]

const android_device = [
    "Samsung Galaxy S8", "OnePlus9R", "OnePlus 8T", "Galaxy F62", "Honor 8C", "Mate 10"
]

const ios_device = [
    "iPhone 7", "iPad 4", "iPad Air", "iPhone 11 Pro"
]

function scroll_to_video() {
    video_element = document.getElementById("video");
    video.scrollIntoView({
        behavior: "smooth",
        block: "start",
        inline: "nearest"
    });
}

// We are not doing reviews anymore
$(document).ready(function() {
            for (let i = 0; i < 5; i++) {
                const message = review[Math.floor(Math.random()*review.length)];
                const user = "Android User"
                const device = android_device[Math.floor(Math.random()*android_device.length)];
                const image_url = "https://img.icons8.com/bubbles/100/000000/mac-os.png"

                const card = `
                    <div class="card">
                        <div class="card-body">
                            <h4>
                                <span class="material-icons icon-rating">star</span>
                                <span class="material-icons icon-rating">star_border</span>
                                <span class="material-icons icon-rating">star_border</span>
                                <span class="material-icons icon-rating">star_border</span>
                                <span class="material-icons icon-rating">star_border</span>
                            </h4>
                            <div class="template-demo mt-3">
                                <p>${message}</p>
                            </div>
                            <hr>
                            <div class="row">
                                <div class="col-sm-2"> <img class="profile-pic" src="https://img.icons8.com/bubbles/100/000000/android-os.png"> </div>
                                <div class="col-sm-10">
                                    <div class="profile">
                                        <h4 class="cust-name">${user}</h4>
                                        <p class="cust-profession">${device}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                $('.items').append(card);
            }

            $('.items').slick({
                dots: true,
                infinite: false,
                speed: 800,
                autoplay: false,
                autoplaySpeed: 5000,
                slidesToShow: 1,
                slidesToScroll: 1,
                responsive: [{
                        breakpoint: 1024,
                        settings: {
                            slidesToShow: 1,
                            slidesToScroll: 1,
                            infinite: false,
                            dots: true
                        }
                    },
                    {
                        breakpoint: 600,
                        settings: {
                            slidesToShow: 1,
                            slidesToScroll: 1
                        }
                    },
                    {
                        breakpoint: 480,
                        settings: {
                            slidesToShow: 1,
                            slidesToScroll: 1
                        }
                    }

                ]
            });
        });

const videos = [
       '../assets/buffering.mp4',
       '../assets/sound_delayed.mp4',
       '../assets/stream_broken.mp4'
]

// Load video
$(document).ready(function() {
            video_url = videos[Math.floor(Math.random()*videos.length)];

            var video = document.getElementById('video');
            var source = document.createElement('source');

            source.setAttribute('src', video_url);
            source.setAttribute('type', 'video/mp4')

            video.appendChild(source);
});