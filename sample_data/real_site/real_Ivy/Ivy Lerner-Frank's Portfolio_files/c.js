/**
 * SparkLoop Conversion Tracking Script
 *
 * This script tracks CPA (Cost-Per-Action) offer conversions on brand websites.
 *
 * Usage:
 * 1. Include this script on your website: <script src="https://c-js.{domain}/c.js"></script>
 * 2. Call SparkLoop.trackConversion("offer_uuid") when a conversion happens
 *
 * The script automatically:
 * - Reads "submission" and "offer" parameters from the URL
 * - Stores submission UUID in a cookie per offer (sl_submission_<offer_uuid>)
 * - Makes cookies available across all subdomains
 * - Supports test_mode via "test_mode" parameter (shorter cookie expiry)
 * - Sends conversion data to SparkLoop when track(offer_uuid) is called
 *
 * This way we are creating a cookie per offer, and we are able to track conversions for multiple offers on the same domain.
 * When a conversion happens, and we pass the offer UUID, we can get the submission UUID from the cookie and send it to the API.
 */

(function() {
  "use strict";

  // Configuration
  const SUBMISSIONS_COOKIE_PREFIX = "sl_submission";
  const SOURCE_COOKIE_PREFIX = "sl_source";
  const TEST_COOKIE_PREFIX = "sl_test";
  const NORMAL_COOKIE_EXPIRE_IN = 30 * 24 * 60 * 60 * 1000; // 30 days
  const TEST_COOKIE_EXPIRE_IN = 15 * 60 * 1000; // 15 minutes

  // IMPORTANT: This method is only used for active development in the cycle,
  // and later will be replaced with the production endpoint.
  // Build API endpoint URL from script's own location
  // Local development: http://localhost:8787/c.js -> https://c-js.sparkloop.local/offer_conversions
  // Production: https://c-js.sparkloop.app/c.js -> https://c-js.sparkloop.app/offer_conversions
  function getApiEndpoint() {
    try {
      // Get the script's source URL
      const scriptSrc = document.currentScript ? document.currentScript.src : "";
      if (scriptSrc) {
        const url = new URL(scriptSrc);

        // Local development: script served from localhost:8787
        if (url.hostname === "localhost" && url.port === "8787") {
          // Use the same protocol as the current page to avoid mixed content errors
          const protocol = window.location.protocol; // 'http:' or 'https:'
          return protocol + "//c-js.sparkloop.local/offer_conversions";
        }

        // Production: use script's own host
        return url.protocol + "//" + url.host + "/offer_conversions";
      }
    } catch (e) {
      console.warn("[SparkLoop Conversion] Could not determine script URL:", e);
    }

    // Fallback: assume production
    return "https://c-js.sparkloop.app/offer_conversions";
  }

  const apiEndpoint = getApiEndpoint();
  console.log("[SparkLoop Conversion] Script initialized. API endpoint:", apiEndpoint);

  /**
   * Cookie utilities
   */
  const Cookie = {
    // Get cookie value by name
    get: function(name) {
      const cookiePrefix = name + "=";
      const cookies = document.cookie.split(";");

      const cookie = cookies.find(function(c) {
        return c.trim().startsWith(cookiePrefix);
      });

      return cookie ? cookie.trim().substring(cookiePrefix.length) : null;
    },

    // Check if cookie exists
    exists: function(name) {
      return this.get(name) !== null;
    },

    // Get the broadest valid domain for subdomain support
    // Uses browser validation to find the correct base domain
    getBaseDomain: function() {
      const hostname = window.location.hostname;
      const parts = hostname.split(".");

      // Handle localhost, IPs, or single-part domains
      if (parts.length < 2) {
        return null;
      }

      // Try progressively larger domain parts until cookie sticks
      // Browser will reject public suffixes (e.g., .com, .co.uk)
      for (let i = 2; i <= parts.length; i++) {
        const candidate = parts.slice(-i).join(".");
        const testCookie = "__test=1; domain=." + candidate + "; path=/";
        document.cookie = testCookie;

        if (document.cookie.indexOf("__test=1") !== -1) {
          // Cookie worked! Clean up test cookie
          document.cookie = "__test=; expires=Thu, 01 Jan 1970 00:00:00 UTC; domain=." + candidate + "; path=/";
          return candidate;
        }
      }

      // Fallback to hostname (shouldn't reach here)
      return hostname;
    },

    // Set cookie (available across all subdomains)
    set: function(name, value, expire_in) {
      const date = new Date();
      date.setTime(date.getTime() + expire_in);
      const expires = "expires=" + date.toUTCString();

      // Get the broadest valid domain
      const baseDomain = this.getBaseDomain();
      const domain = baseDomain ? ";domain=." + baseDomain : "";

      document.cookie = name + "=" + value + ";" + expires + ";path=/" + domain + ";SameSite=Lax";

      console.log("[SparkLoop Conversion] Cookie set:", name, value, expire_in / (1000 * 60 * 60 * 24), "days", "domain:", baseDomain || "current");
      console.log("[SparkLoop Conversion] Cookie document.cookie:", document.cookie);
    },

    // Get all cookies matching a prefix, returns object {cookieName: value}
    getAllByPrefix: function(prefix) {
      const result = {};
      const cookies = document.cookie.split(";");
      const prefixPattern = prefix + "_";

      cookies.forEach(function(cookie) {
        cookie = cookie.trim();
        if (cookie.startsWith(prefixPattern)) {
          const equalIndex = cookie.indexOf("=");
          const cookieName = cookie.substring(0, equalIndex);
          const cookieValue = cookie.substring(equalIndex + 1);
          result[cookieName] = cookieValue;
        }
      });

      return result;
    }
  };

  /**
   * Get URL parameter value
   */
  function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
  }

  /**
   * Check if we're in test mode
   */
  function isTestMode() {
    return getUrlParameter("test_mode") === "true";
  }

  /**
   * Store submission UUID in cookie named by offer UUID
   */
  function trackPageVisit() {
    const submissionUuid = getUrlParameter("submission");
    const offerUuid = getUrlParameter("offer");

    if (!submissionUuid) {
      // No submission parameter, nothing to track
      console.log("[SparkLoop Conversion] No submission parameter in URL, skipping tracking");
      return;
    }

    if (!offerUuid) {
      // No offer parameter, nothing to track
      console.log("[SparkLoop Conversion] No offer parameter in URL, skipping tracking");
      return;
    }

    console.log("[SparkLoop Conversion] Submission parameter found:", submissionUuid);
    console.log("[SparkLoop Conversion] Offer parameter found:", offerUuid);

    // Build dynamic cookie name using offer UUID
    const cookieName = SUBMISSIONS_COOKIE_PREFIX + "_" + offerUuid;

    // Check if this offer UUID cookie already exists
    if (Cookie.exists(cookieName)) {
      // Offer already tracked, skip (preserves original expiry timer)
      console.log("[SparkLoop Conversion] Cookie already exists for offer:", offerUuid);
      return;
    }

    const testMode = isTestMode();
    const cookieExpiry = testMode ? TEST_COOKIE_EXPIRE_IN : NORMAL_COOKIE_EXPIRE_IN;

    // Store submission UUID in cookie
    Cookie.set(cookieName, submissionUuid, cookieExpiry);

    // Store source param in cookie (e.g., "nudge_email" from nudge email links)
    const source = getUrlParameter("sl_source");
    if (source) {
      const sourceCookieName = SOURCE_COOKIE_PREFIX + "_" + offerUuid;
      Cookie.set(sourceCookieName, source, cookieExpiry);
    }

    if (testMode) {
      const testCookieName = TEST_COOKIE_PREFIX + "_" + offerUuid;
      Cookie.set(testCookieName, "true", TEST_COOKIE_EXPIRE_IN);

      console.log("[SparkLoop Conversion] Test mode: Cookie set for 15 minutes");
    } else {
      console.log("[SparkLoop Conversion] Normal mode: Cookie set for 30 days");
    }
  }

  /**
   * Send conversion event to SparkLoop
   */
  function sendConversionEvent(offerUuid) {
    console.log("[SparkLoop Conversion] track() called with offer UUID:", offerUuid);

    // Build dynamic cookie name and get submission UUID
    const cookieName = SUBMISSIONS_COOKIE_PREFIX + "_" + offerUuid;
    const submissionUuid = Cookie.get(cookieName);

    if (!submissionUuid) {
      console.warn("[SparkLoop Conversion] No submission UUID found for offer:", offerUuid);
      return;
    }

    console.log("[SparkLoop Conversion] Found submission UUID:", submissionUuid, "for offer:", offerUuid);

    const testCookieName = TEST_COOKIE_PREFIX + "_" + offerUuid;
    const testMode = Cookie.get(testCookieName) == "true";

    const sourceCookieName = SOURCE_COOKIE_PREFIX + "_" + offerUuid;
    const source = Cookie.get(sourceCookieName);

    const payload = {
      submission_uuid: submissionUuid,
      offer_uuid: offerUuid,
      test_mode: testMode,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      sl_source: source
    };

    console.log("[SparkLoop Conversion] Sending payload:", payload);

    // Send to SparkLoop API
    fetch(apiEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      keepalive: true,
    })
    .then(function(response) {
      if (response.ok) {
        console.log("[SparkLoop Conversion] Conversion tracked successfully. Status:", response.status);
      } else {
        console.error("[SparkLoop Conversion] Failed to track conversion:", response.status);
      }
    })
    .catch(function(error) {
      console.error("[SparkLoop Conversion] Error tracking conversion:", error);
    });
  }

  /**
   * Initialize tracking on page load
   */
  function init() {
    trackPageVisit();
  }

  /**
   * Expose global API
   */
  window.SparkLoop = {
    trackConversion: function(offerUuid) {
      if (!offerUuid) {
        console.error("[SparkLoop Conversion] Offer UUID is required");
        return;
      }

      sendConversionEvent(offerUuid);
    },

    // Expose for debugging - returns object {cookieName: submissionUuid}
    getSubmissions: function() {
      return Cookie.getAllByPrefix(SUBMISSIONS_COOKIE_PREFIX);
    },

    isTestMode: isTestMode
  };

  // Auto-initialize on script load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
