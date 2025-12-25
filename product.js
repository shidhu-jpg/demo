fetch("products.json")
  .then(res => res.json())
  .then(products => {
    const container = document.getElementById("product-container");

    products.forEach((product, index) => {
      const swiperClass = `swiper-${index}`;

      let slides = "";
      product.images.forEach(img => {
        if (!product.images || product.images.length < 2) {
            return;
}

        slides += `
          <div class="swiper-slide">
            <a href="${img}" class="glightbox" data-gallery="${product.category}">
              <img src="${img}" />
            </a>
          </div>
        `;
      });

      const html = `
        <div class="product-card">
          <div class="swiper ${swiperClass}">
            <div class="swiper-wrapper">
              ${slides}
            </div>
            <div class="swiper-button-next"></div>
            <div class="swiper-button-prev"></div>
          </div>

          <div class="product-details">
            <h2>${product.title}</h2>
            <p>${product.description || ""}</p>
          </div>
        </div>
      `;

      container.insertAdjacentHTML("beforeend", html);

      new Swiper(`.${swiperClass}`, {
        loop: true,
        navigation: {
          nextEl: ".swiper-button-next",
          prevEl: ".swiper-button-prev"
        }
      });
    });

    GLightbox({ selector: ".glightbox" });
  })
  .catch(err => console.error("Failed to load products:", err));
