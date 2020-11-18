$('.get').on('click', function() {
    $(this).html('<i class="fa fa-spinner fa-pulse fa-fw"></i> loading...')
    $('main').css( 'pointer-events', 'none' );
})

$(document).ready(function() {
    let caption = $('.caption');
        if (caption.height() > 250) {
            caption.slimScroll({
                size: '5px',
                borderRadius: '0px',
                color: '#869791',
                opacity: 0.8,
                alwaysVisible: true,
                distance: '0px',
            });
        }
})

$(document).ready(function() {
    if ($('.content-flex').length != 0) {
        $('html, body').animate({
            scrollTop: $('.content-flex').offset().top
        }, 400);
    }
})
