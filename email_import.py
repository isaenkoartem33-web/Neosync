import imaplib
import email
from email.header import decode_header
import re
from datetime import date, timedelta


class EmailImporter:
    def __init__(self, email_address, password):
        self.email_address = email_address
        self.password = password
        self.imap = None

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except Exception:
                pass

    def decode_subject(self, subject):
        if not subject:
            return ""
        parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                try:
                    parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                except Exception:
                    parts.append(part.decode('utf-8', errors='ignore'))
            else:
                parts.append(str(part))
        return ' '.join(parts)

    def get_email_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = str(part.get("Content-Disposition"))
                if ct == "text/plain" and "attachment" not in cd:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode('utf-8', errors='ignore')
                    except Exception:
                        pass
                elif ct == "text/html" and not body and "attachment" not in cd:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            html = payload.decode('utf-8', errors='ignore')
                            body += re.sub(r'<[^>]+>', ' ', html)
                    except Exception:
                        pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            except Exception:
                pass
        return body

    def parse_subscription_from_email(self, subject, body_or_sender):
        """Parse subscription from subject + sender (body optional)"""
        amount_patterns = [
            (r'(\d+(?:[.,]\d{2})?)\s*(?:₽|руб\.?|RUB)', 'RUB'),
            (r'(?:₽|руб\.?|RUB)\s*(\d+(?:[.,]\d{2})?)', 'RUB'),
            (r'(\d+(?:[.,]\d{2})?)\s*(?:USD|\$)', 'USD'),
            (r'\$\s*(\d+(?:[.,]\d{2})?)', 'USD'),
            (r'(\d+(?:[.,]\d{2})?)\s*(?:EUR|€)', 'EUR'),
            (r'€\s*(\d+(?:[.,]\d{2})?)', 'EUR'),
            (r'(?:сумма|итого|total|amount|к оплате|к списанию)[:\s]+(\d+(?:[.,]\d{2})?)', 'RUB'),
        ]

        period_patterns = {
            'monthly': r'(?:ежемесячн|месяц|monthly|month|per month|/month)',
            'yearly': r'(?:ежегодн|год|yearly|annual|year|per year|/year)',
            'weekly': r'(?:еженедельн|недел|weekly|week|per week|/week)',
            'quarterly': r'(?:квартал|quarterly|quarter)',
        }

        subscription_keywords = [
            'subscription', 'подписк', 'membership', 'членство',
            'recurring', 'повторяющ', 'автоплатеж', 'autopay',
            'renewal', 'продление', 'payment', 'оплата',
            'invoice', 'счет', 'receipt', 'квитанц', 'чек',
            'списание', 'billing', 'заказ', 'покупка', 'purchase',
            'спасибо за', 'thank you', 'confirmed', 'подтвержд',
        ]

        # Известные сервисы в отправителе — сразу считаем подпиской
        known_senders = [
            'netflix', 'spotify', 'apple', 'google', 'yandex', 'adobe',
            'microsoft', 'openai', 'github', 'notion', 'dropbox', 'skillbox',
            'geekbrains', 'noreply', 'no-reply', 'billing', 'payments',
        ]

        text = (subject + ' ' + body_or_sender).lower()
        is_subscription = any(kw in text for kw in subscription_keywords)
        is_known_sender = any(s in body_or_sender.lower() for s in known_senders)
        has_amount_in_subject = bool(re.search(r'\d+[.,]\d{2}', subject))

        if not is_subscription and not is_known_sender and not has_amount_in_subject:
            return None

        amount = None
        currency = 'RUB'
        for pattern, cur in amount_patterns:
            match = re.search(pattern, subject + ' ' + body_or_sender, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', '.'))
                    currency = cur
                    break
                except Exception:
                    continue

        billing_period = 'monthly'
        for period, pattern in period_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                billing_period = period
                break

        subject_parts = re.split(r'[:\-–—]', subject)
        service_name = subject_parts[0].strip() if subject_parts else "Подписка"
        service_name = re.sub(
            r'\b(payment|оплата|invoice|счет|receipt|квитанция|subscription|подписка|чек|списание)\b',
            '', service_name, flags=re.IGNORECASE
        ).strip()
        if len(service_name) < 3:
            # Попробуем взять имя из отправителя
            sender_match = re.search(r'([A-Za-zА-Яа-я]{3,})', body_or_sender)
            service_name = sender_match.group(1).capitalize() if sender_match else "Подписка"
        if len(service_name) > 50:
            service_name = service_name[:50]

        category = 'Other'
        category_map = {
            'Entertainment': ['netflix', 'spotify', 'youtube', 'apple music', 'яндекс', 'yandex',
                               'кинопоиск', 'okko', 'ivi', 'premier', 'more.tv', 'wink', 'megogo'],
            'Software': ['adobe', 'microsoft', 'office', 'chatgpt', 'github', 'jetbrains',
                         'notion', 'dropbox', 'google', 'cloud', 'облако', 'mail.ru', 'openai'],
            'Education': ['coursera', 'udemy', 'skillshare', 'duolingo', 'stepik',
                          'geekbrains', 'skillbox', 'нетология', 'netology'],
            'Health': ['fitness', 'gym', 'спорт', 'тренажер', 'worldclass', 'fitmost'],
        }
        sl = service_name.lower()
        for cat, keywords in category_map.items():
            if any(kw in sl for kw in keywords):
                category = cat
                break

        return {
            'name': service_name,
            'cost': amount,
            'currency': currency,
            'billing_period': billing_period,
            'category': category,
            'complete': amount is not None,
        }

    def _imap_search(self, query):
        """Поиск с поддержкой UTF-8 через CHARSET"""
        try:
            # Сначала пробуем с CHARSET UTF-8 (поддерживается Яндексом)
            status, messages = self.imap.search('UTF-8', query)
            if status == 'OK' and messages[0]:
                return messages[0].split()
        except Exception:
            pass
        try:
            # Fallback — ASCII только (без кириллицы)
            status, messages = self.imap.search(None, query)
            if status == 'OK' and messages[0]:
                return messages[0].split()
        except Exception:
            pass
        return []

    def search_subscription_emails(self, max_results=100, days_back=365):
        if not self.imap:
            return []
        try:
            self.imap.select('INBOX')
            date_since = (date.today() - timedelta(days=days_back)).strftime("%d-%b-%Y")

            # Кириллические запросы — через UTF-8 CHARSET
            cyrillic_queries = [
                f'(SINCE {date_since} SUBJECT "подписка")',
                f'(SINCE {date_since} SUBJECT "оплата")',
                f'(SINCE {date_since} SUBJECT "счет")',
                f'(SINCE {date_since} SUBJECT "квитанция")',
                f'(SINCE {date_since} SUBJECT "чек")',
                f'(SINCE {date_since} SUBJECT "списание")',
                f'(SINCE {date_since} SUBJECT "продление")',
                f'(SINCE {date_since} SUBJECT "заказ")',
                f'(SINCE {date_since} SUBJECT "покупка")',
            ]
            # ASCII запросы — работают везде
            ascii_queries = [
                f'(SINCE {date_since} SUBJECT "subscription")',
                f'(SINCE {date_since} SUBJECT "payment")',
                f'(SINCE {date_since} SUBJECT "invoice")',
                f'(SINCE {date_since} SUBJECT "receipt")',
                f'(SINCE {date_since} SUBJECT "renewal")',
                f'(SINCE {date_since} SUBJECT "billing")',
                f'(SINCE {date_since} FROM "netflix")',
                f'(SINCE {date_since} FROM "spotify")',
                f'(SINCE {date_since} FROM "apple")',
                f'(SINCE {date_since} FROM "google")',
                f'(SINCE {date_since} FROM "yandex")',
                f'(SINCE {date_since} FROM "adobe")',
                f'(SINCE {date_since} FROM "microsoft")',
                f'(SINCE {date_since} FROM "openai")',
                f'(SINCE {date_since} FROM "github")',
                f'(SINCE {date_since} FROM "notion")',
                f'(SINCE {date_since} FROM "noreply")',
                f'(SINCE {date_since} FROM "no-reply")',
                f'(SINCE {date_since} FROM "billing")',
                f'(SINCE {date_since} FROM "payments")',
            ]

            all_ids = set()
            for query in cyrillic_queries:
                all_ids.update(self._imap_search(query))
            for query in ascii_queries:
                try:
                    status, messages = self.imap.search(None, query)
                    if status == 'OK' and messages[0]:
                        all_ids.update(messages[0].split())
                except Exception:
                    continue

            # Fallback — последние 200 писем если ничего не нашли
            if not all_ids:
                try:
                    status, messages = self.imap.search(None, f'SINCE {date_since}')
                    if status == 'OK' and messages[0]:
                        ids = messages[0].split()
                        all_ids.update(ids[-200:])
                except Exception:
                    pass

            subscriptions = []
            seen = set()
            for eid in list(all_ids)[:max_results]:
                try:
                    # Берём только заголовки — намного быстрее чем RFC822
                    status, msg_data = self.imap.fetch(eid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
                    if status != 'OK':
                        continue
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    subject = self.decode_subject(msg.get('Subject', ''))
                    sender = msg.get('From', '')
                    # Для парсинга суммы используем только тему — тело не грузим
                    info = self.parse_subscription_from_email(subject, sender)
                    if info and info['complete']:
                        key = info['name'].lower()
                        if key not in seen:
                            seen.add(key)
                            subscriptions.append(info)
                except Exception as e:
                    print(f"Error processing email {eid}: {e}")
            return subscriptions
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []


class YandexImporter(EmailImporter):
    IMAP_SERVER = 'imap.yandex.ru'
    IMAP_PORT = 993

    def connect(self):
        try:
            print(f"[YANDEX] Подключаемся к {self.IMAP_SERVER}:{self.IMAP_PORT} как {self.email_address}")
            self.imap = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
            self.imap.login(self.email_address, self.password)
            print(f"[YANDEX] Успешно подключились!")
            return True
        except Exception as e:
            print(f"[YANDEX] Ошибка подключения: {e}")
            return False


class MailRuImporter(EmailImporter):
    IMAP_SERVER = 'imap.mail.ru'
    IMAP_PORT = 993

    def connect(self):
        try:
            print(f"[MAILRU] Подключаемся к {self.IMAP_SERVER}:{self.IMAP_PORT} как {self.email_address}")
            self.imap = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
            self.imap.login(self.email_address, self.password)
            print(f"[MAILRU] Успешно подключились!")
            return True
        except Exception as e:
            print(f"[MAILRU] Ошибка подключения: {e}")
            return False


def import_from_email(provider, email_address, password, max_results=100):
    if provider == 'yandex':
        importer = YandexImporter(email_address, password)
    elif provider == 'mailru':
        importer = MailRuImporter(email_address, password)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    try:
        if not importer.connect():
            return {'error': 'Не удалось подключиться к почтовому серверу. Проверьте email и пароль приложения.', 'subscriptions': []}
        subscriptions = importer.search_subscription_emails(max_results=max_results)
        return {'success': True, 'subscriptions': subscriptions, 'count': len(subscriptions)}
    except Exception as e:
        return {'error': str(e), 'subscriptions': []}
    finally:
        importer.disconnect()
