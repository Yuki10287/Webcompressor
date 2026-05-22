var pixel_v2 = (function (exports) {
  'use strict';

  const version = "2.2.1";

  function generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === "x" ? r : r & 3 | 8;
      return v.toString(16);
    });
  }
  function isCrawler() {
    const ua = navigator.userAgent.toLowerCase();
    const crawlerRegex = /(bot|crawl|spider|slurp|archiver|indexer|facebookexternalhit|twitterbot|bingpreview|applebot|siteaudit|semrush|ahrefs|mj12bot|seznambot|screaming frog|dotbot)/i;
    return crawlerRegex.test(ua);
  }
  function getInt(s) {
    if (typeof s === "number") return s;
    if (typeof s === "string") return Number.parseInt(s, 10);
    return void 0;
  }
  function validatePixelId(pixelId) {
    if (!pixelId || typeof pixelId !== "string") {
      throw new Error("Invalid pixel ID");
    }
    const pixelIdRegex = /^[a-zA-Z0-9-_]{8,}$/;
    if (!pixelIdRegex.test(pixelId)) {
      throw new Error("Invalid pixel ID format");
    }
    return true;
  }
  function isValidClickId(bhclId) {
    return /^[a-zA-Z0-9-_]{8,}$/.test(bhclId);
  }

  const EXCLUDED_DOMAINS = ["beehiiv.com", "staginghiiv.com", "localhiiv.com"];
  const COOKIE_MAX_AGE_SECONDS = 365 * 24 * 60 * 60;
  function getHostDomain(hostname) {
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return { host: "", domain: "localhost" };
    }
    let host = "www";
    let domain = "";
    const parts = hostname.split(".");
    if (parts.length < 3) {
      domain = `${parts[0]}.${parts[1]}`;
    } else {
      host = parts[0];
      domain = `${parts[1]}.${parts[2]}`;
    }
    return { host, domain };
  }
  function parseClickId(url) {
    try {
      const parsed = new URL(url);
      const bhclId = parsed.searchParams.get("bhcl_id");
      if (!bhclId) return null;
      if (!isValidClickId(bhclId)) {
        console.error("Invalid bhcl_id format");
        return null;
      }
      return bhclId;
    } catch {
      return null;
    }
  }
  class DocumentCookieJar {
    constructor(host, domain) {
      this.host = host;
      this.domain = domain;
    }
    isSecure = true;
    async get(name) {
      const [cookie] = this.findCookieWithHost(name);
      return cookie ? cookie.split("=")[1] : "";
    }
    async set(name, value) {
      const isExcludedDomain = EXCLUDED_DOMAINS.includes(this.domain);
      const effectiveName = isExcludedDomain && name === "_bhc" ? `${name}_${this.host}` : name;
      const props = `domain=.${this.domain}; path=/; samesite=strict; ${this.isSecure ? "secure;" : ""} max-age=${COOKIE_MAX_AGE_SECONDS}`;
      document.cookie = `${effectiveName}=${value}; ${props}`;
    }
    findCookieWithHost(name) {
      const allCookies = document.cookie.split(";");
      let cookie;
      const isExcludedDomain = EXCLUDED_DOMAINS.includes(this.domain);
      if (!isExcludedDomain) {
        cookie = this.findCookie(allCookies, name);
      }
      if (!cookie) {
        const hostScoped = `${name}_${this.host}`;
        cookie = this.findCookie(allCookies, hostScoped);
        if (cookie) return [cookie, hostScoped];
      }
      if (!cookie && this.host !== "www") {
        const wwwScoped = `${name}_www`;
        cookie = this.findCookie(allCookies, wwwScoped);
        if (cookie) return [cookie, wwwScoped];
      }
      return [cookie, name];
    }
    findCookie(allCookies, name) {
      return allCookies.find((cookie) => cookie.trim().startsWith(`${name}=`));
    }
  }

  const STORAGE_KEY = "bhpx_processed_events";
  const DEDUPE_TIME_PERIOD_SECONDS = 15 * 60;
  function hashString(str) {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = (hash << 5) + hash + str.charCodeAt(i) | 0;
    }
    return (hash >>> 0).toString(36);
  }
  function dedupe(events) {
    const currentTime = Math.floor(Date.now() / 1e3);
    let processedEvents = {};
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) processedEvents = JSON.parse(stored);
    } catch (error) {
      console.warn("Failed to load processed events from localStorage:", error);
    }
    const seen = /* @__PURE__ */ new Set();
    const filtered = events.filter((event) => {
      const eventHash = hashEventForDedupe(event);
      if (seen.has(eventHash)) return false;
      if (processedEvents[eventHash]) {
        const age = currentTime - processedEvents[eventHash];
        if (age < DEDUPE_TIME_PERIOD_SECONDS) return false;
      }
      seen.add(eventHash);
      return true;
    });
    const updated = { ...processedEvents };
    filtered.forEach((event) => {
      updated[hashEventForDedupe(event)] = currentTime;
    });
    Object.keys(updated).forEach((hash) => {
      if (updated[hash] < currentTime - DEDUPE_TIME_PERIOD_SECONDS) {
        delete updated[hash];
      }
    });
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
      console.warn("Failed to save processed events to localStorage:", error);
    }
    return filtered;
  }
  function hashEventForDedupe(event) {
    const { timestamp, landed_timestamp, sent_timestamp, event_id, ...rest } = event;
    return hashString(JSON.stringify(rest));
  }

  async function hashEmail(email) {
    if (!email) {
      return { email_hash_sha256: "", email_hash_sha1: "" };
    }
    const [email_hash_sha256, email_hash_sha1] = await Promise.all([
      generateHash(email, "SHA-256"),
      generateHash(email, "SHA-1")
    ]);
    return { email_hash_sha256, email_hash_sha1 };
  }
  async function generateHash(input, algorithm) {
    const msgBuffer = new TextEncoder().encode(input);
    const hashBuffer = await crypto.subtle.digest(algorithm, msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  async function buildPayload(ctx) {
    const event_id = generateUUID();
    const timestamp = Date.now();
    const [bhc, bhp] = await Promise.all([ctx.cookies.get("_bhc"), ctx.cookies.get("_bhp")]);
    const [ad_network_placement_id, subscriber_id, email_address_id] = bhc.split("_");
    let email = ctx.data.email || "";
    if (!email) {
      try {
        const url = new URL(ctx.url);
        email = url.searchParams.get("email") || "";
      } catch {
      }
    }
    const { email_hash_sha256, email_hash_sha1 } = await hashEmail(email);
    return {
      pixel_id: ctx.pixelId,
      ad_network_placement_id: ad_network_placement_id || "",
      subscriber_id: subscriber_id || "",
      profile_id: bhp,
      event: ctx.eventName,
      timestamp,
      landed_timestamp: timestamp,
      sent_timestamp: timestamp,
      event_id,
      url: ctx.url,
      user_agent: ctx.userAgent,
      script_version: ctx.scriptVersion,
      content_category: ctx.data.content_category,
      content_ids: ctx.data.content_ids,
      content_name: ctx.data.content_name,
      content_type: ctx.data.content_type,
      currency: ctx.data.currency,
      num_items: ctx.data.num_items,
      predicted_ltv_cents: getInt(ctx.data.predicted_ltv_cents),
      search_string: ctx.data.search_string,
      status: ctx.data.status,
      value_cents: getInt(ctx.data.value_cents),
      email_hash_sha256,
      email_hash_sha1,
      order_id: ctx.data.order_id,
      email_address_id
    };
  }

  const APIARY_ENDPOINT = "https://ingestion.prod.apiarydata.net/api/v2/ingestion/pixel";
  const DEFAULT_CONFIG = {
    retryAttempts: 3,
    retryDelay: 1e3
  };
  async function sendToApiary(payloads, config = {}) {
    if (payloads.length === 0) return;
    const cfg = { ...DEFAULT_CONFIG, ...config };
    const body = JSON.stringify(payloads);
    if (typeof navigator !== "undefined" && navigator.sendBeacon) {
      const sent = navigator.sendBeacon(APIARY_ENDPOINT, body);
      if (sent) return;
    }
    await sendWithRetry(body, cfg, 0);
  }
  async function sendWithRetry(body, cfg, attempt) {
    try {
      const response = await fetch(APIARY_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true
      });
      if (!response.ok && response.status >= 500 && attempt < cfg.retryAttempts) {
        throw new Error(`apiary returned ${response.status}`);
      }
    } catch (err) {
      if (attempt < cfg.retryAttempts) {
        await new Promise((resolve) => setTimeout(resolve, cfg.retryDelay * (attempt + 1)));
        return sendWithRetry(body, cfg, attempt + 1);
      }
      throw err;
    }
  }

  const bhpx = window.bhpx;
  const queue = bhpx.queue || [];
  let _pixelId = "";
  let _cookies = null;
  let _initPromise = null;
  const CONFIG = {
    BATCH_SIZE: 1,
    BATCH_INTERVAL: 1e3,
    DISABLE_DEDUPE: false,
    DEBUG: false
  };
  function debugLog(...args) {
    if (CONFIG.DEBUG) {
      console.log("[bhpx]", ...args);
    }
  }
  const eventQueue = [];
  let batchTimeout = null;
  function isInitialized() {
    if (!_initPromise) {
      throw new Error('Pixel not initialized — call bhpx("init", "PIXEL_ID") first');
    }
    return _initPromise;
  }
  async function init(pixelId, options = {}) {
    try {
      validatePixelId(pixelId);
      _pixelId = pixelId;
      const { host, domain } = getHostDomain(window.location.hostname);
      _cookies = new DocumentCookieJar(host, domain);
      debugLog(`beehiiv pixel v${version} initialized`);
      const config = {
        autoConfig: true,
        debug: false,
        disableDedupe: false,
        trackClientNavigation: true,
        batchSize: CONFIG.BATCH_SIZE,
        batchInterval: CONFIG.BATCH_INTERVAL,
        ...options
      };
      Object.assign(CONFIG, {
        BATCH_SIZE: config.batchSize,
        BATCH_INTERVAL: config.batchInterval,
        DISABLE_DEDUPE: config.disableDedupe,
        DEBUG: config.debug
      });
      if (!await _cookies.get("_bhp")) {
        await _cookies.set("_bhp", generateUUID());
      }
      const bhclId = parseClickId(window.location.href);
      if (bhclId) {
        const existing = await _cookies.get("_bhc");
        if (existing !== bhclId) {
          await _cookies.set("_bhc", bhclId);
          debugLog(`bhcl_id captured: ${bhclId}`);
        }
      }
      if (config.trackClientNavigation) {
        monitorUrlChanges(() => track("pageview"));
      }
      if (config.debug) {
        enableDebugMode();
      }
    } catch (error) {
      console.error("Initialization failed:", error);
      throw error;
    }
  }
  async function track(eventName, options = {}) {
    try {
      if (isCrawler()) return;
      await isInitialized();
      const pixelId = options.pixelId || _pixelId;
      if (!pixelId) throw new Error("Pixel ID not initialized");
      if (options.pixelId) validatePixelId(options.pixelId);
      if (!eventName || typeof eventName !== "string") {
        throw new Error("Invalid event name");
      }
      if (!_cookies) throw new Error("Cookie jar not initialized");
      const payload = await buildPayload({
        pixelId,
        eventName: eventName.toLowerCase(),
        url: window.location.href,
        userAgent: window.navigator.userAgent,
        scriptVersion: version,
        cookies: _cookies,
        data: options.data || {}
      });
      const debug = window.bhpx?.debug;
      if (debug && typeof debug === "object" && "log" in debug) {
        debug.log(`track: ${eventName} ${JSON.stringify(options.data || {})}`);
      }
      eventQueue.push(payload);
      if (!batchTimeout && eventQueue.length < CONFIG.BATCH_SIZE) {
        batchTimeout = setTimeout(processBatch, CONFIG.BATCH_INTERVAL);
      } else if (eventQueue.length >= CONFIG.BATCH_SIZE) {
        await processBatch();
      }
    } catch (error) {
      console.error("Tracking failed:", error);
    }
  }
  async function processBatch() {
    if (eventQueue.length === 0) return;
    const drained = eventQueue.splice(0, CONFIG.BATCH_SIZE);
    const batch = CONFIG.DISABLE_DEDUPE ? drained : dedupe(drained);
    batchTimeout = null;
    if (batch.length === 0) return;
    try {
      await sendToApiary(batch);
    } catch (error) {
      console.error("Failed to process batch:", error);
      eventQueue.unshift(...batch);
    }
  }
  debugLog(`beehiiv pixel v${version} loaded`);
  bhpx.callMethod = (...rest) => {
    const args = Array.prototype.slice.call(rest);
    const method = args[0];
    const params = args.slice(1);
    switch (method) {
      case "init": {
        _initPromise = init(params[0], params[1]);
        break;
      }
      case "track": {
        const trackFn = window.bhp?.track || track;
        trackFn(params[0], params[1]);
        break;
      }
      default: {
        console.error(`Unknown method: ${method}`);
      }
    }
  };
  while (queue.length > 0) {
    const cmd = queue.shift();
    if (cmd) bhpx.callMethod.apply(null, cmd);
  }
  function monitorUrlChanges(onUrlChange) {
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    function triggerUrlChangeEvent() {
      window.dispatchEvent(new Event("bhpx:urlchange"));
    }
    history.pushState = function(...args) {
      originalPushState.apply(this, args);
      triggerUrlChangeEvent();
    };
    history.replaceState = function(...args) {
      originalReplaceState.apply(this, args);
      triggerUrlChangeEvent();
    };
    window.addEventListener("popstate", triggerUrlChangeEvent);
    window.addEventListener("bhpx:urlchange", onUrlChange);
  }
  function enableDebugMode() {
    window.bhpx.debug = true;
    const debugStyles = {
      group: "color: #4a90e2; font-weight: bold; font-size: 12px;",
      event: "color: #2ecc71; font-weight: bold;",
      params: "color: #9b59b6;"
    };
    const debugOverlay = document.createElement("div");
    debugOverlay.style.cssText = `
    position: fixed; bottom: 20px; right: 20px;
    background: rgba(0,0,0,0.8); color: white;
    padding: 10px; border-radius: 5px;
    font-family: monospace; font-size: 12px;
    z-index: 9999; max-height: 300px; overflow-y: auto; max-width: 400px;
  `;
    document.body.appendChild(debugOverlay);
    function logToOverlay(message) {
      const entry = document.createElement("div");
      entry.style.borderBottom = "1px solid rgba(255,255,255,0.1)";
      entry.style.padding = "5px 0";
      entry.textContent = `${(/* @__PURE__ */ new Date()).toISOString().slice(11, -1)} - ${message}`;
      debugOverlay.insertBefore(entry, debugOverlay.firstChild);
      if (debugOverlay.children.length > 50) {
        debugOverlay.removeChild(debugOverlay.lastChild);
      }
    }
    const originalTrack = window.bhpx.track || track;
    window.bhpx.track = async function(eventName, params = {}) {
      console.group("%cBeehiiv Pixel Debug", debugStyles.group);
      console.log(`%cEvent: ${eventName.toLowerCase()}`, debugStyles.event);
      console.log("%cParameters:", debugStyles.params, params);
      console.log("%cRouting Info:", debugStyles.params, {
        pathname: window.location.pathname,
        search: window.location.search,
        hash: window.location.hash,
        title: document.title,
        referrer: document.referrer
      });
      console.groupEnd();
      logToOverlay(`${eventName} tracked - ${JSON.stringify(params)}`);
      await originalTrack.apply(this, [eventName, params]);
    };
    window.bhpx.debug = {
      overlay: debugOverlay,
      clearLogs: () => {
        debugOverlay.innerHTML = "";
      },
      toggleOverlay: () => {
        debugOverlay.style.display = debugOverlay.style.display === "none" ? "block" : "none";
      },
      getEventHistory: () => Array.from(debugOverlay.children).map((c) => c.textContent || ""),
      log: logToOverlay
    };
    console.log(
      "%cBeehiiv Pixel Debug Mode Enabled",
      "color: #4a90e2; font-size: 14px; font-weight: bold;"
    );
  }

  exports.CONFIG = CONFIG;
  exports.init = init;
  exports.isInitialized = isInitialized;
  exports.track = track;

  Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });

  return exports;

})({});
