import zh from './content/zh.json';
import en from './content/en.json';
export const dict = { zh, en };
const base = import.meta.env.BASE_URL.replace(/\/$/, '');
export const pages = { home: '', services: 'services/', research: 'open-source/', about: 'about/', contact: 'contact/', checkup: 'checkup/' };
export const url = (lang, key) => `${base}/${lang === 'en' ? 'en/' : ''}${pages[key]}`;
export const asset = (p) => `${base}/${p}`;
