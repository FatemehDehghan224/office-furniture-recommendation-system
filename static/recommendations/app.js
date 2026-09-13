const form = document.querySelector("#recommendation-form");
const errorBox = document.querySelector("#form-error");
const resultList = document.querySelector("#result-list");
const resultCount = document.querySelector("#result-count");

const labels = {
    "office desk": "میز اداری",
    "office chair": "صندلی اداری",
    "file cabinet": "فایلینگ",
    bookshelf: "کتابخانه",
    "reception counter": "کانتر پذیرش",
    "waiting area sofa": "مبل انتظار",
};

function payloadFromForm(formElement) {
    const raw = Object.fromEntries(new FormData(formElement).entries());
    const payload = {
        person: raw.person,
        productType: raw.productType,
        number_of_person: Number(raw.number_of_person),
    };
    for (const field of ["budget", "budget_min", "budget_max"]) {
        if (raw[field] !== "") payload[field] = Number(raw[field]);
    }
    for (const field of ["style", "color", "fabric_material", "body_material"]) {
        if (raw[field] !== "") payload[field] = raw[field];
    }
    return payload;
}

function renderProducts(items) {
    resultCount.textContent = `${items.length} پیشنهاد`;
    if (!items.length) {
        resultList.innerHTML = '<p class="empty-state">برای این نقش و نوع محصول، گزینه‌ای در کاتالوگ وجود ندارد.</p>';
        return;
    }
    resultList.innerHTML = items.map(({ rank, score, product }) => `
        <article class="product">
            <div class="product-title">
                <h3>${labels[product.productType] || product.productType} شماره ${product.id}</h3>
                <span class="rank">رتبه ${rank}</span>
            </div>
            <div class="meta">
                <span>${Number(product.budget).toLocaleString("fa-IR")} تومان</span>
                <span>ظرفیت ${product.number_of_person} نفر</span>
                <span>سبک ${product.style}</span>
                <span>رنگ ${product.color}</span>
                <span>امتیاز تطابق ${score}</span>
            </div>
        </article>
    `).join("");
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.hidden = true;
    const button = form.querySelector("button[type=submit]");
    button.disabled = true;
    try {
        const response = await fetch("/api/v1/recommendations/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payloadFromForm(form)),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(Object.values(data).flat().join(" "));
        renderProducts(data.recommendations);
    } catch (error) {
        errorBox.textContent = error.message || "دریافت پیشنهادها با خطا مواجه شد.";
        errorBox.hidden = false;
    } finally {
        button.disabled = false;
    }
});
