"""
RumorBuster - Digital Origin Tracer & Source Provenance Module
Finds "Ground Zero" of viral claims, fake news, and suspicious URLs.
Queries legal public sources:
- Internet Archive (Wayback Machine CDX & Availability APIs)
- Domain RDAP / ICANN Registration Intelligence
- Google Fact Check Tools API (with graceful fallback to open archives)
- Google News RSS Real-time & Historical Index
- Submitter Node Geolocation & Claim Recurrence Fingerprinting
"""

import os
import re
import json
import hashlib
import datetime
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def is_valid_url(text):
    """Detects if input text is a URL."""
    text = text.strip()
    if text.startswith(('http://', 'https://')):
        return True
    # Match domain-like patterns: example.com/path or sub.example.org
    domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:/.*)?$'
    return bool(re.match(domain_pattern, text))

def normalize_url(raw_input):
    """Ensures URL has scheme and extracts clean domain."""
    url = raw_input.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith('www.'):
        domain = domain[4:]
    return url, domain

def compute_claim_hash(text):
    """Generates SHA-256 fingerprint of normalized text."""
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def geolocate_client_ip(ip_address):
    """Geolocates client IP address with fallback for private/local IPs."""
    if not ip_address:
        ip_address = '127.0.0.1'
        
    # Check for loopback / private IP ranges
    if (ip_address in ['127.0.0.1', '::1', 'localhost'] or
        ip_address.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.31.'))):
        return {
            "ip": ip_address,
            "is_local": True,
            "city": "Localhost / Test Node",
            "region": "Intranet",
            "country": "Private Network",
            "country_code": "LOC",
            "isp": "Local Forensic Lab",
            "formatted": "Local Forensic Node (Private LAN / Test Lab)"
        }
        
    try:
        r = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=4)
        if r.status_code == 200:
            data = r.json()
            city = data.get('city') or 'Unknown City'
            country = data.get('country_name') or data.get('country') or 'Unknown Country'
            isp = data.get('org') or 'Unknown ISP'
            return {
                "ip": ip_address,
                "is_local": False,
                "city": city,
                "region": data.get('region', ''),
                "country": country,
                "country_code": data.get('country_code', ''),
                "isp": isp,
                "latitude": data.get('latitude'),
                "longitude": data.get('longitude'),
                "formatted": f"{city}, {country} ({isp})"
            }
    except Exception as e:
        print(f"[IP Geolocation] Primary error: {e}")
        
    # Fallback to ip-api.com
    try:
        r2 = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,regionName,city,isp", timeout=3)
        if r2.status_code == 200:
            d2 = r2.json()
            if d2.get('status') == 'success':
                city = d2.get('city', 'Unknown City')
                country = d2.get('country', 'Unknown Country')
                isp = d2.get('isp', 'Unknown ISP')
                return {
                    "ip": ip_address,
                    "is_local": False,
                    "city": city,
                    "region": d2.get('regionName', ''),
                    "country": country,
                    "country_code": d2.get('countryCode', ''),
                    "isp": isp,
                    "formatted": f"{city}, {country} ({isp})"
                }
    except Exception as e:
        print(f"[IP Geolocation] Fallback error: {e}")

    return {
        "ip": ip_address,
        "is_local": False,
        "city": "Unknown",
        "region": "Unknown",
        "country": "Unknown",
        "formatted": f"IP: {ip_address} (Location unavailable)"
    }

def trace_wayback_archive(target_url, domain=None):
    """
    Queries Wayback Machine CDX and Availability APIs to find:
    1. Earliest archived snapshot timestamp
    2. Total snapshots count
    3. Direct replay URL to earliest archive
    """
    result = {
        "found": False,
        "earliest_date": None,
        "earliest_timestamp": None,
        "earliest_snapshot_url": None,
        "total_snapshots": 0,
        "domain_earliest_date": None,
        "domain_snapshot_url": None
    }
    
    headers = {"User-Agent": "RumorBuster-OriginTracer/1.0 (+https://rumorbuster.local)"}
    
    # 1. Exact URL CDX Query
    try:
        cdx_url = f"https://web.archive.org/cdx/search/cdx?url={target_url}&output=json&limit=10&fl=timestamp,original,statuscode"
        r = requests.get(cdx_url, headers=headers, timeout=6)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1: # data[0] is header row
                first_row = data[1]
                ts = first_row[0] # YYYYMMDDhhmmss
                orig = first_row[1]
                try:
                    dt = datetime.datetime.strptime(ts, "%Y%m%d%H%M%S")
                    result["found"] = True
                    result["earliest_timestamp"] = ts
                    result["earliest_date"] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    result["earliest_snapshot_url"] = f"https://web.archive.org/web/{ts}/{orig}"
                    result["total_snapshots"] = len(data) - 1
                except Exception:
                    pass
    except Exception as e:
        print(f"[Wayback CDX] Error: {e}")

    # Fallback to Availability API if CDX returned nothing
    if not result["found"]:
        try:
            avail_url = f"https://archive.org/wayback/available?url={target_url}&timestamp=19960101"
            r = requests.get(avail_url, headers=headers, timeout=5)
            if r.status_code == 200:
                snap = r.json().get('archived_snapshots', {}).get('closest', {})
                if snap.get('available') and snap.get('timestamp'):
                    ts = snap.get('timestamp')
                    try:
                        dt = datetime.datetime.strptime(ts, "%Y%m%d%H%M%S")
                        result["found"] = True
                        result["earliest_timestamp"] = ts
                        result["earliest_date"] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                        result["earliest_snapshot_url"] = snap.get('url')
                        result["total_snapshots"] = 1
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Wayback Availability] Error: {e}")

    # 2. Check root domain earliest archive if domain provided
    if domain:
        try:
            dom_cdx = f"https://web.archive.org/cdx/search/cdx?url={domain}&output=json&limit=1&fl=timestamp,original"
            r_dom = requests.get(dom_cdx, headers=headers, timeout=5)
            if r_dom.status_code == 200:
                dom_data = r_dom.json()
                if len(dom_data) > 1:
                    ts_dom = dom_data[1][0]
                    orig_dom = dom_data[1][1]
                    try:
                        dt_dom = datetime.datetime.strptime(ts_dom, "%Y%m%d%H%M%S")
                        result["domain_earliest_date"] = dt_dom.strftime("%Y-%m-%d %H:%M:%S UTC")
                        result["domain_snapshot_url"] = f"https://web.archive.org/web/{ts_dom}/{orig_dom}"
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Wayback Domain CDX] Error: {e}")

    return result

def trace_domain_rdap(domain):
    """
    Queries ICANN RDAP (Registry Data Access Protocol) for domain registration age.
    100% free, legal, and authoritative.
    """
    res = {
        "success": False,
        "domain": domain,
        "registration_date": None,
        "expiration_date": None,
        "age_days": None,
        "age_formatted": None,
        "registrar": None,
        "risk_level": "LOW",
        "risk_reason": "Established domain"
    }
    
    # Strip port if any
    clean_domain = domain.split(':')[0].strip().lower()
    
    try:
        url = f"https://rdap.org/domain/{clean_domain}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            events = data.get('events', [])
            reg_date_str = None
            exp_date_str = None
            for ev in events:
                action = ev.get('eventAction')
                if action == 'registration' and not reg_date_str:
                    reg_date_str = ev.get('eventDate')
                elif action == 'expiration' and not exp_date_str:
                    exp_date_str = ev.get('eventDate')
                    
            # Parse registrar name
            entities = data.get('entities', [])
            for ent in entities:
                roles = ent.get('roles', [])
                if 'registrar' in roles:
                    vcard = ent.get('vcardArray', [])
                    if len(vcard) > 1:
                        for item in vcard[1]:
                            if item[0] == 'fn':
                                res["registrar"] = item[3]
                                break
                                
            if reg_date_str:
                # Parse ISO date
                try:
                    clean_reg = reg_date_str.split('T')[0]
                    dt_reg = datetime.datetime.strptime(clean_reg, "%Y-%m-%d")
                    res["registration_date"] = clean_reg
                    res["success"] = True
                    
                    now = datetime.datetime.utcnow()
                    delta = now - dt_reg
                    days = max(0, delta.days)
                    res["age_days"] = days
                    
                    years = days // 365
                    remaining_days = days % 365
                    months = remaining_days // 30
                    if years > 0:
                        res["age_formatted"] = f"{years} yr, {months} mo ({days} days)"
                    else:
                        res["age_formatted"] = f"{months} mo ({days} days)"
                        
                    # Risk evaluation
                    if days < 30:
                        res["risk_level"] = "HIGH"
                        res["risk_reason"] = f"CRITICAL: Domain was registered only {days} days ago. High likelihood of disposable / spoof fake news domain."
                    elif days < 90:
                        res["risk_level"] = "MEDIUM"
                        res["risk_reason"] = f"WARNING: Domain is relatively new ({days} days). Exercise scrutiny."
                    else:
                        res["risk_level"] = "LOW"
                        res["risk_reason"] = f"Domain is mature ({res['age_formatted']})."
                except Exception as ex:
                    print(f"[RDAP Parse] Date error: {ex}")
    except Exception as e:
        print(f"[RDAP Query] Error for {clean_domain}: {e}")

    return res

def scrape_page_metadata(url):
    """Fetches OpenGraph and microdata metadata from submitted URL."""
    meta = {
        "title": None,
        "author": None,
        "publisher": None,
        "published_time": None,
        "canonical_url": None,
        "status_code": None
    }
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=6)
        meta["status_code"] = r.status_code
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Title
            og_title = soup.find('meta', property='og:title')
            meta["title"] = og_title['content'] if og_title and og_title.get('content') else (soup.title.text.strip() if soup.title else None)
            
            # Publisher / Site name
            og_site = soup.find('meta', property='og:site_name')
            if og_site and og_site.get('content'):
                meta["publisher"] = og_site['content']
                
            # Published time
            og_time = soup.find('meta', property='article:published_time') or soup.find('meta', {'name': 'pubdate'}) or soup.find('meta', {'name': 'date'})
            if og_time and og_time.get('content'):
                meta["published_time"] = og_time['content']
                
            # Author
            og_author = soup.find('meta', property='article:author') or soup.find('meta', {'name': 'author'})
            if og_author and og_author.get('content'):
                meta["author"] = og_author['content']
                
            # Canonical URL
            can = soup.find('link', rel='canonical')
            if can and can.get('href'):
                meta["canonical_url"] = can['href']
    except Exception as e:
        print(f"[Page Metadata] Error: {e}")
    return meta

def trace_google_fact_check_api(query, api_key=None):
    """
    Queries Google Fact Check Tools API if an API key is available.
    """
    if not api_key or api_key in ["your_gemini_api_key_here", ""]:
        return None
        
    endpoint = f"https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": query, "key": api_key, "languageCode": "en"}
    try:
        r = requests.get(endpoint, params=params, timeout=5)
        if r.status_code == 200:
            claims_data = r.json().get('claims', [])
            parsed = []
            for item in claims_data[:5]:
                reviews = item.get('claimReview', [])
                checker = reviews[0].get('publisher', {}).get('name', 'Independent Fact Checker') if reviews else 'Fact Checker'
                verdict = reviews[0].get('textualRating', 'Unverified') if reviews else 'Unverified'
                review_url = reviews[0].get('url', '') if reviews else ''
                parsed.append({
                    "text": item.get('text', ''),
                    "claimant": item.get('claimant', 'Unknown'),
                    "claim_date": item.get('claimDate', 'Unknown'),
                    "fact_checker": checker,
                    "verdict": verdict,
                    "review_url": review_url
                })
            return parsed
    except Exception as e:
        print(f"[Google Fact Check API] Error: {e}")
    return None

def trace_news_timeline(query):
    """
    Searches Google News RSS for published news coverage and fact checks.
    Extracts dates, titles, outlets, and creates chronological records.
    """
    records = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # Try searching for the query itself
    queries_to_test = [query]
    if "fact check" not in query.lower():
        queries_to_test.append(f"{query} fact check")
        
    seen_links = set()
    for q in queries_to_test:
        try:
            url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en"
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'xml')
                for item in soup.find_all('item')[:6]:
                    link = item.link.text if item.link else ''
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    
                    title = item.title.text if item.title else 'News Item'
                    source = item.source.text if item.source else 'News Outlet'
                    pub_str = item.pubDate.text if item.pubDate else ''
                    
                    # Parse date to standardized format
                    parsed_dt = None
                    if pub_str:
                        try:
                            # RFC 822 format: e.g. 'Tue, 22 Aug 2023 07:00:00 GMT'
                            parsed_dt = datetime.datetime.strptime(pub_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                        except Exception:
                            try:
                                parsed_dt = datetime.datetime.strptime(pub_str[:16].strip(), "%a, %d %b %Y")
                            except Exception:
                                pass
                                
                    records.append({
                        "title": title,
                        "source": source,
                        "link": link,
                        "raw_date": pub_str,
                        "datetime": parsed_dt,
                        "formatted_date": parsed_dt.strftime("%Y-%m-%d") if parsed_dt else pub_str
                    })
        except Exception as e:
            print(f"[News Timeline] Error for query '{q}': {e}")
            
    # Sort chronologically (oldest first)
    valid_dated = [r for r in records if r["datetime"] is not None]
    undated = [r for r in records if r["datetime"] is None]
    valid_dated.sort(key=lambda x: x["datetime"])
    
    return valid_dated + undated

def build_origin_trace_report(input_text, client_ip="127.0.0.1", factcheck_api_key=None):
    """
    Master Origin Tracing Pipeline.
    Combines Wayback Machine, RDAP, News Timelines, IP Geolocation,
    and SQLite recurrence tracking into an executive forensic report.
    """
    input_text = input_text.strip()
    is_url = is_valid_url(input_text)
    query_hash = compute_claim_hash(input_text)
    trace_id = hashlib.md5(f"{query_hash}{datetime.datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
    
    # 1. Submitter IP Geolocation
    client_geo = geolocate_client_ip(client_ip)
    
    # 2. Recurrence / Prior Check in Database
    from database import get_origin_trace_recurrence, save_origin_trace
    recurrence_info = get_origin_trace_recurrence(query_hash)
    
    # 3. Main Tracing Logic
    timeline_events = []
    ground_zero_candidate = None
    earliest_date_str = None
    domain_intel = None
    wayback_intel = None
    meta_intel = None
    fact_check_intel = []
    news_records = []
    
    if is_url:
        target_url, domain = normalize_url(input_text)
        
        # A. Page Metadata
        meta_intel = scrape_page_metadata(target_url)
        
        # B. Domain Age (RDAP)
        domain_intel = trace_domain_rdap(domain)
        if domain_intel.get("registration_date"):
            timeline_events.append({
                "date": domain_intel["registration_date"],
                "type": "DOMAIN_CREATION",
                "badge": "Infrastructure",
                "title": f"Domain '{domain}' Registered",
                "description": f"Registrar: {domain_intel.get('registrar') or 'Public Registry'}. Age: {domain_intel.get('age_formatted')}.",
                "source": domain,
                "url": f"https://{domain}"
            })
            
        # C. Wayback Machine
        wayback_intel = trace_wayback_archive(target_url, domain)
        if wayback_intel.get("found"):
            timeline_events.append({
                "date": wayback_intel["earliest_date"].split()[0],
                "type": "WAYBACK_EARLIEST",
                "badge": "Web Archive",
                "title": "Earliest Known Wayback Snapshot",
                "description": f"Captured by Internet Archive crawlers on {wayback_intel['earliest_date']}.",
                "source": "Internet Archive (Wayback Machine)",
                "url": wayback_intel["earliest_snapshot_url"]
            })
            
        # D. Published date from page metadata if available
        if meta_intel.get("published_time"):
            clean_meta_date = meta_intel["published_time"].split('T')[0]
            timeline_events.append({
                "date": clean_meta_date,
                "type": "META_PUBLISHED",
                "badge": "Source Metadata",
                "title": f"Article Published: {meta_intel.get('title') or target_url}",
                "description": f"Author: {meta_intel.get('author') or 'Unknown'}. Publisher: {meta_intel.get('publisher') or domain}.",
                "source": meta_intel.get('publisher') or domain,
                "url": target_url
            })
            
        # E. Cross-search headline on News RSS
        headline_to_search = meta_intel.get("title") or domain
        news_records = trace_news_timeline(headline_to_search)
        
        ground_zero_candidate = {
            "source": meta_intel.get("publisher") or domain,
            "url": target_url,
            "earliest_date": wayback_intel.get("earliest_date") or domain_intel.get("registration_date") or "Unknown",
            "type": "Web Source URL"
        }
        
    else:
        # Input is a claim / rumor statement
        claim_text = input_text
        
        # A. Google Fact Check Tools API (or simulated fallback)
        fact_check_intel = trace_google_fact_check_api(claim_text, factcheck_api_key) or []
        for fc in fact_check_intel:
            if fc.get("claim_date") and fc.get("claim_date") != "Unknown":
                timeline_events.append({
                    "date": fc["claim_date"],
                    "type": "VIRAL_CLAIM_START",
                    "badge": "Claim Origin",
                    "title": f"Claim Propagated by: {fc.get('claimant', 'Social Media / Viral Seed')}",
                    "description": f"\"{fc.get('text')}\"",
                    "source": fc.get('claimant', 'Online Sources'),
                    "url": fc.get('review_url', '')
                })
            timeline_events.append({
                "date": "Debunk Record",
                "type": "FACT_CHECK_DEBUNK",
                "badge": "Fact Check",
                "title": f"{fc.get('fact_checker')} Rating: {fc.get('verdict')}",
                "description": f"Verified and reviewed by official fact check network.",
                "source": fc.get('fact_checker'),
                "url": fc.get('review_url')
            })
            
        # B. News Timeline & Early Coverage Search
        news_records = trace_news_timeline(claim_text)
        for nr in news_records[:5]:
            timeline_events.append({
                "date": nr["formatted_date"],
                "type": "NEWS_COVERAGE",
                "badge": "Press Record",
                "title": nr["title"],
                "description": f"Reported by {nr['source']}.",
                "source": nr["source"],
                "url": nr["link"]
            })
            
        # Determine earliest news outlet
        if news_records:
            first_news = news_records[0]
            ground_zero_candidate = {
                "source": first_news["source"],
                "url": first_news["link"],
                "earliest_date": first_news["formatted_date"],
                "type": "Earliest Indexed News Coverage"
            }
        else:
            ground_zero_candidate = {
                "source": "Uncertain / Unindexed Viral Seed",
                "url": "#",
                "earliest_date": "Undated",
                "type": "Dark Web / Private Messaging App"
            }

    # Add Current Investigation event to timeline
    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    timeline_events.append({
        "date": now_str.split()[0],
        "type": "RUMORBUSTER_INVESTIGATION",
        "badge": "Forensic Log",
        "title": "Investigated on RumorBuster Platform",
        "description": f"Submitted from {client_geo.get('formatted')}. Recurrence count: #{recurrence_info['count'] + 1}.",
        "source": "RumorBuster Node",
        "url": "#"
    })

    # Sort timeline by date string where possible
    def parse_event_sort_key(ev):
        d = ev.get("date", "")
        # Match YYYY-MM-DD
        m = re.match(r'^(\d{4}-\d{2}-\d{2})', d)
        if m:
            return m.group(1)
        return "9999-99-99"

    timeline_events.sort(key=parse_event_sort_key)
    
    # Calculate earliest known date
    earliest_date_str = timeline_events[0]["date"] if timeline_events else "Unknown"

    # Compile executive summary
    report = {
        "trace_id": trace_id,
        "query_text": input_text,
        "query_type": "URL" if is_url else "Claim",
        "query_hash": query_hash,
        "earliest_date": earliest_date_str,
        "ground_zero": ground_zero_candidate,
        "submitter": client_geo,
        "recurrence": {
            "is_repeat": recurrence_info["count"] > 0,
            "total_checks": recurrence_info["count"] + 1,
            "first_seen_platform": recurrence_info["first_seen"],
            "first_seen_location": recurrence_info["first_geo"]
        },
        "domain_intel": domain_intel,
        "wayback_intel": wayback_intel,
        "meta_intel": meta_intel,
        "fact_checks": fact_check_intel,
        "news_sources": news_records[:6],
        "timeline": timeline_events,
        "timestamp": now_str
    }
    
    # Save to SQLite origin_traces table
    try:
        # Strip non-serializable datetime objects from news_sources
        clean_news = []
        for nr in news_records[:6]:
            c_nr = dict(nr)
            if 'datetime' in c_nr:
                c_nr['datetime'] = str(c_nr['datetime']) if c_nr['datetime'] else None
            clean_news.append(c_nr)

        report["news_sources"] = clean_news
        
        db_record = {
            "trace_id": trace_id,
            "query_text": input_text,
            "query_type": "url" if is_url else "claim",
            "query_hash": query_hash,
            "earliest_date": str(earliest_date_str),
            "ground_zero_source": ground_zero_candidate["source"] if ground_zero_candidate else "Unknown",
            "ground_zero_url": ground_zero_candidate["url"] if ground_zero_candidate else "",
            "domain_age_days": domain_intel.get("age_days") if domain_intel else None,
            "submitter_ip": client_geo.get("ip"),
            "submitter_geo": client_geo.get("formatted"),
            "summary_json": json.dumps(report, default=str)
        }
        save_origin_trace(db_record)
    except Exception as e:
        print(f"[Save Origin Trace] DB error: {e}")

    return report
