// 全局变量
let config = null;
let currentLang = 'zh';

// 翻译映射
const translations = {
  nav: {
    home: { zh: '首页', en: 'Home' },
    products: { zh: '产品中心', en: 'Products' },
    about: { zh: '关于我们', en: 'About Us' },
    contact: { zh: '联系我们', en: 'Contact Us' }
  },
  products: {
    title: { zh: '产品中心', en: 'Products' },
    subtitle: { zh: 'Our Products', en: '' }
  },
  about: {
    title: { zh: '关于我们', en: 'About Us' },
    subtitle: { zh: 'About Us', en: '' }
  },
  contact: {
    title: { zh: '联系我们', en: 'Contact Us' },
    subtitle: { zh: 'Get In Touch', en: '' },
    phone: { zh: '电话', en: 'Phone' },
    email: { zh: '邮箱', en: 'Email' },
    address: { zh: '地址', en: 'Address' },
    formTitle: { zh: '在线留言', en: 'Leave a Message' },
    name: { zh: '姓名', en: 'Name' },
    email: { zh: '邮箱', en: 'Email' },
    phone: { zh: '电话', en: 'Phone' },
    company: { zh: '单位', en: 'Company' },
    message: { zh: '留言内容', en: 'Message' },
    submit: { zh: '提交', en: 'Submit' }
  },
  hero: {
    cta: { zh: '查看产品', en: 'View Products' }
  },
  common: {
    features: { zh: '产品特点', en: 'Features' },
    parameters: { zh: '技术参数', en: 'Specifications' },
    noImage: { zh: '暂无图片', en: 'No Image' }
  }
};

// 加载配置
async function loadConfig() {
  try {
    const response = await fetch('config.json');
    config = await response.json();
    renderAll();
  } catch (error) {
    console.error('加载配置失败:', error);
    document.body.innerHTML = '<div class="loading">加载配置失败，请刷新页面</div>';
  }
}

// 渲染所有内容
function renderAll() {
  renderCompanyInfo();
  renderHero();
  renderProducts();
  renderAbout();
  renderContact();
  setupEventListeners();
}

// 渲染公司信息
function renderCompanyInfo() {
  const company = config.company;
  document.getElementById('companyName').textContent = company.name;
  document.getElementById('footerCompany').textContent = company.name;
  document.title = company.name;
}

// 渲染首页横幅
function renderHero() {
  const hero = config.sections.home;
  const title = currentLang === 'zh' ? hero.heroTitle : hero.heroTitleEn;
  const subtitle = currentLang === 'zh' ? hero.heroSubtitle : hero.heroSubtitleEn;
  document.getElementById('heroTitle').textContent = title;
  document.getElementById('heroSubtitle').textContent = subtitle;
}

// 渲染产品列表
function renderProducts() {
  const grid = document.getElementById('productsGrid');
  const products = config.products;
  
  grid.innerHTML = products.map((product, index) => `
    <div class="product-card" onclick="showProductDetail(${index})">
      <div class="product-image">
        ${product.image ? `<img src="${product.image}" alt="${product.name}" onerror="this.parentElement.innerHTML='${translations.common.noImage[currentLang]}'">` : translations.common.noImage[currentLang]}
      </div>
      <div class="product-info">
        <div class="product-category">${product.category}</div>
        <h3 class="product-name">${currentLang === 'zh' ? product.name : product.nameEn}</h3>
        <p class="product-desc">${currentLang === 'zh' ? product.description : product.descriptionEn}</p>
        <div class="product-features">
          ${product.features.slice(0, 3).map(f => `<span class="product-tag">${f}</span>`).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

// 显示产品详情
function showProductDetail(index) {
  const product = config.products[index];
  const modal = document.getElementById('productModal');
  const body = document.getElementById('modalBody');
  
  const params = product.parameters;
  const paramsHtml = Object.entries(params).map(([key, value]) => `
    <div class="param-item">
      <span class="param-label">${key}</span>
      <span class="param-value">${value}</span>
    </div>
  `).join('');
  
  const featuresHtml = product.features.map(f => `<span class="product-tag">${f}</span>`).join('');
  
  body.innerHTML = `
    <img src="${product.image || ''}" alt="${product.name}" class="modal-image" onerror="this.style.display='none'">
    <h2 class="modal-title">${currentLang === 'zh' ? product.name : product.nameEn}</h2>
    <div class="modal-category">${product.category}</div>
    <p class="modal-desc">${currentLang === 'zh' ? product.description : product.descriptionEn}</p>
    
    <div class="modal-section">
      <h3>${translations.common.features[currentLang]}</h3>
      <div class="product-features" style="margin-bottom: 25px;">${featuresHtml}</div>
    </div>
    
    <div class="modal-section">
      <h3>${translations.common.parameters[currentLang]}</h3>
      <div class="modal-params">${paramsHtml}</div>
    </div>
  `;
  
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

// 渲染关于
function renderAbout() {
  const about = config.sections.about;
  const content = currentLang === 'zh' ? about.content : about.contentEn;
  document.getElementById('aboutContent').textContent = content;
}

// 渲染联系
function renderContact() {
  const company = config.company;
  document.getElementById('contactPhone').textContent = company.phone;
  document.getElementById('contactEmail').textContent = company.email;
  document.getElementById('contactAddress').textContent = company.address;
}

// 切换语言
function toggleLanguage() {
  currentLang = currentLang === 'zh' ? 'en' : 'zh';
  document.getElementById('langToggle').textContent = currentLang === 'zh' ? 'EN' : '中';
  renderAll();
}

// 设置事件监听
function setupEventListeners() {
  // 移动端导航
  document.getElementById('navToggle').addEventListener('click', () => {
    document.getElementById('navMenu').classList.toggle('active');
  });
  
  // 语言切换
  document.getElementById('langToggle').addEventListener('click', toggleLanguage);
  
  // 弹窗关闭
  document.getElementById('modalClose').addEventListener('click', closeModal);
  document.getElementById('productModal').addEventListener('click', (e) => {
    if (e.target.id === 'productModal') closeModal();
  });
  
  // 表单提交
  document.getElementById('contactForm').addEventListener('submit', handleFormSubmit);
  
  // 滚动监听
  window.addEventListener('scroll', handleScroll);
}

// 关闭弹窗
function closeModal() {
  document.getElementById('productModal').classList.remove('active');
  document.body.style.overflow = '';
}

// 表单提交
function handleFormSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);
  
  alert('感谢您的留言！我们会尽快与您联系。');
  form.reset();
}

// 滚动处理
function handleScroll() {
  const navbar = document.querySelector('.navbar');
  if (window.scrollY > 50) {
    navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.15)';
  } else {
    navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
  }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', loadConfig);
