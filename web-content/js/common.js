/**
 * Project Clearwater - IMS in the Cloud
 * Copyright (C) 2013  Metaswitch Networks Ltd
 *
 * This program is free software: you can redistribute it and/or modify it 
 * under the terms of the GNU General Public License as published by the 
 * Free Software Foundation, either version 3 of the License, or (at your 
 * option) any later version, along with the “Special Exception” for use of 
 * the program along with SSL, set forth below. This program is distributed 
 * in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
 * A PARTICULAR PURPOSE.  See the GNU General Public License for more 
 * details. You should have received a copy of the GNU General Public 
 * License along with this program.  If not, see 
 * <http://www.gnu.org/licenses/>.
 *
 * The author can be reached by email at clearwater@metaswitch.com or by 
 * post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
 *
 * Special Exception
 * Metaswitch Networks Ltd  grants you permission to copy, modify, 
 * propagate, and distribute a work formed by combining OpenSSL with The 
 * Software, or a work derivative of such a combination, even if such 
 * copying, modification, propagation, or distribution would otherwise 
 * violate the terms of the GPL. You must comply with the GPL in all 
 * respects for all of the code used other than OpenSSL.
 * "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL 
 * Project and licensed under the OpenSSL Licenses, or a work based on such 
 * software and licensed under the OpenSSL Licenses.
 * "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License 
 * under which the OpenSSL Project distributes the OpenSSL toolkit software,
 * as those licenses appear in the file LICENSE-OPENSSL.
 */

var clearwater = (function(mod, $){ 
  
  // The URL-specific JS should fill these in.
  mod.pages = {};
  
  function setDefaultPage(page) {
    mod.pages[""] = page;
  }
  mod.setDefaultPage = setDefaultPage;
  
  function addPage(page) {
    mod.pages[page.name] = page;
  }
  mod.addPage = addPage;
  
  // ---------------------------------------------------------------------------
  // Utility functions
  // ---------------------------------------------------------------------------
  function log(msg) {
    try{
      console.log(msg);
    } catch (e) {
      // Browser doesn't support console.
    }
  }
  mod.log = log;

  PARAM_HISTORY_ID = "u";
  PARAM_LOCATION = "l";
  
  function indexOf(obj) {
    for (var i = 0; i < this.length; i++) {
      if (obj === this[i]) {
        return i;
      }
    }
  }
  
  if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = indexOf;
  }
  
  function removeFromArray(ar, obj) {
    var idx = ar.indexOf(obj);
    if (idx >= 0) {
      ar.splice(idx, 1);
    }
  }
  
  function parseUrl(url) {
    url = url || location.href.toString();
    var result = {};
    var len = url.length;
    var hashIdx = url.indexOf("#");
    if (hashIdx >= 0) {
      result["hash"] = url.substring(hashIdx, len);
      url = url.substring(0, hashIdx);
    }
    var query = "";
    var qmIdx = url.indexOf("?");
    if (qmIdx >= 0) {
      query = url.substring(qmIdx+1, len);
      url = url.substring(0, qmIdx);
    }
    var keyValues = query.split("&");
    var queryParams = {};
    for (var i = 0; i < keyValues.length; i++) {
      var kv = keyValues[i];
      var equalsIdx = kv.indexOf("=");
      var key;
      var value;
      if (equalsIdx >= 0) {
        key = decodeURIComponent(kv.substring(0, equalsIdx));
        value = decodeURIComponent(kv.substring(equalsIdx+1, kv.length));
      } else {
        key = kv;
        value = true;
      }
      queryParams[key] = value;
    }
    result["query"] = query;
    result["params"] = queryParams;
    return result;
  }
  mod.parseUrl = parseUrl;
  
  function dictToQueryString(dict) {
    var sep = "";
    var qs = "";
    for (var key in dict) {
      if (dict.hasOwnProperty(key)) {
        qs += sep + encodeURIComponent(key) + "=" + encodeURIComponent(dict[key]);
        sep = "&";
      }
    }
    return qs;
  };
  mod.dictToQueryString = dictToQueryString;
  
  /**
   * Triggers a navigation to the given page with the given parameters.  The
   * result is to trigger a hash change event which will then trigger the 
   * navigation.
   */
  function goToPage(page, pageParams) {
    if (page == undefined) {
      // The link clicked has no associated page, so execute defualt action
      return true;
    }

    if (pageParams === null || pageParams === undefined) {
      pageParams = {};
    }
    var paramsCopy = copyJsonObject(pageParams);
    paramsCopy[PARAM_HISTORY_ID] = getCb();
    paramsCopy[PARAM_LOCATION] = page.name;
    jQuery.bbq.pushState(paramsCopy);
    return false;
  }
  mod.goToPage = goToPage;
  
  /**
   * Constructs a URL for the action of a form, embedding the onsuccess and
   * onfailure parameters.  the onfailure is calculated to refer to this page.
   */
  function setFormAction(formSelector, action, successUrl) {
    var ourUrl = location.pathname + location.hash;
    var params = {"onsuccess": successUrl,
                  "onfailure": ourUrl};
    var sep = action.indexOf("?") < 0 ? "?" : "&";
    var url = action + sep + dictToQueryString(params);
    $(formSelector).attr("action", url);
  };
  mod.setFormAction = setFormAction;
  
  function addUrlParameters(url, params)
  {
    var hash = "";
    var hashIdx = url.indexOf("#");
    var len = url.length;
    if (hashIdx >=0 ) {
      // Hash part comes after the query string so we need to save it off.
      hash = url.substring(hashIdx, len);
      url = url.substring(0, hashIdx);
    }
    sep = url.indexOf("?") >=0 ? "&" : "?";
    if (url.lastIndexOf(sep) == len-1) {
      sep = "";
    }
    for (var key in params) {
      if (params.hasOwnProperty(key)) {
        url += sep + encodeURIComponent(key) + "=" + 
               encodeURIComponent(params[key]);
        sep = "&";
      }
    }
    return url + hash;
  }
  
  /**
   * Class that represents a page.
   * 
   * @param name the name used to select this page in URLs.
   * @param selector The jQuery selector to fade in for this page.
   */
  function Page(name, selector) {
    if (!(this instanceof Page)) {
      throw "Page is a class, not a function.";
    }
    this.selector = selector;
    this.name = name;
    this.firstDisplay = true;
    this.template = $(selector).html();
    this.inProgressRequests = [];
    
    mod.addPage(this);
  }
  
  /**
   * Called before restoreState.  Should reset the page to its initial 
   * configuration.
   */
  Page.prototype.resetPage = function() {
    if (!this.firstDisplay) {
      $(this.selector).html(this.template);
      rewriteUrls(this.selector);
    }
    this.firstDisplay = false;
  };
  
  /**
   * Restores the state of the page.  Called before fading in the page.
   * 
   * @param savedState The value returned by getState when hibernating the 
   *         page or null for a fresh instance of the page.
   */
  Page.prototype.restoreState = function(savedState) {};
  
  /**
   * Called when the fade in of the page is cancelled.  Should cancel any HTTP
   * requests in progress, for example.
   */
  Page.prototype.cancel = function() {
    log("Cancelling any in-progress HTTP requests.");
    while (this.inProgressRequests.length) {
      var req = this.inProgressRequests.pop();
      req.abort();
    }
  };

  function getHttp(url, data) {
    data["cb"] = getCb();
    var req = jQuery.get(url, data);
    return req;
  }

  function postHttp(url, data) {
    url = addUrlParameters(url, {"cb": getCb()});
    var req = jQuery.post(url, data);
    return req;
  }

  function putHttp(url, data) {
    url = addUrlParameters(url, {"cb": getCb()});
    var req = jQuery.ajax({
      "url": url,
      "type": "PUT",
      "data": data
    });
    return req;
  }
  
  function deleteHttp(url) {
    url = addUrlParameters(url, {"cb": getCb()});
    var req = jQuery.ajax({
      "url": url,
      "type": "DELETE"
    });
    return req;
  }
  
  function reportError(request) {
    console.log(request.responseText);
  }

  Page.prototype.getHttp = function(url, data) {
    log("Getting " + url);
    var req = getHttp(url, data);
    req.fail(function(data) {
      alert("Failed to retrieve some data from the server.  Please refresh the page.");
      reportError(data);
    });
    this.addInProgressReq(req);
    return req;
  };  

  Page.prototype.postHttp = function(url, data) {
    log("Posting to " + url);
    var req = postHttp(url, data);
    req.fail(function(data) {
      alert("Failed to update the server.  Please refresh the page.");
      reportError(data);
    });
    this.addInProgressReq(req);
    return req;
  };

  Page.prototype.putHttp = function(url, data) {
    log("Putting to " + url);
    var req = putHttp(url, data);
    req.fail(function(data) {
      alert("Failed to update the server.  Please refresh the page.");
      reportError(data);
    });
    this.addInProgressReq(req);
    return req;
  };  

  Page.prototype.deleteHttp = function(url, data) {
    log("Deleting " + url);
    var req = deleteHttp(url, data);
    req.fail(function(data) {
      alert("Failed to delete from the server.  Please try again.");
      reportError(data);
    });
    this.addInProgressReq(req);
    return req;
  };
  
  Page.prototype.addInProgressReq = function(req) {
    var that = this;
    req.always(function() {
      removeFromArray(that.inProgressRequests, req);
    });
    this.inProgressRequests.push(req);
  };
  
  /**
   * Called when the page finishes fading in.
   */
  Page.prototype.onFadeInComplete = function() {};
  
  /**
   * Called when hiding the page.  The state will be stored and passed back
   * to the page when it needs to be restored.
   * 
   * @return the state of the page as a dictionary suitable for JSON 
   *          serialization.
   */
  Page.prototype.getState = function() {};

  mod.Page = Page;
  mod.pleaseWaitPage = new Page("pleasewait", "#please-wait");
  addPage(mod.pleaseWaitPage);
  mod.currentPage = mod.pleaseWaitPage;

  var animationInProgress = false;
  var pageToFadeOut = null;
  var pageToFadeIn = null;
  var pageToFadeInParams = null;
  var currentPageHistoryKey = null;
  
  /**
   * Fades out the current page, fades in the new page.  Handles persisting the
   * old state and recreating the new.
   */
  function changePage(newPage, pageParams) {
    log("Changing page from " + mod.currentPage.name + " to " + newPage.name);
    
    if (currentPageHistoryKey)
    {
      var stateToSave = mod.currentPage.getState();
      putHistory(currentPageHistoryKey, stateToSave);
    }
    
    var oldPageToFadeIn = pageToFadeIn;
    pageToFadeIn = newPage;
    pageToFadeInParams = pageParams;
    if (animationInProgress) {
      if (!pageToFadeOut) {
        // We must be fading in the wrong element.  Stop that fade and 
        // fade it out instead.
        oldPageToFadeIn.cancel();
        $(oldPageToFadeIn.selector).stop();
        pageToFadeOut = oldPageToFadeIn;
        doTransition();
      }
    } else {
      pageToFadeOut = mod.currentPage;
      doTransition();
    }
    
    mod.currentPage = newPage;
    currentPageHistoryKey = pageParams[PARAM_HISTORY_ID];
    
    function doTransition() {
      animationInProgress = true;
      $(pageToFadeOut.selector).fadeOut(function() {
        log("Fade out complete, fading in...");
        pageToFadeOut = null;
        var newState = getHistory(pageToFadeInParams[PARAM_HISTORY_ID]);
        pageToFadeIn.resetPage();
        pageToFadeIn.restoreState(pageToFadeInParams, newState);
        $(pageToFadeIn.selector).fadeIn(function() {
          animationInProgress = false;
          pageToFadeIn.onFadeInComplete();
          pageToFadeIn = null;
          pageToFadeInParams = null;
        });
      });
    }
  }
  
  // Calculate a likely-unique prefix for the cache-breaker generator.  To make
  // a cache breaker we combine:
  //  - the page load time, using a recent epoch to reduce the size of the 
  //    value (this helps when we're using the value in a long URL or in a 
  //    cookie)
  //  - a random separator
  //  - a sequence number.
  var CB_EPOCH = 1336594395000;
  var CB_SEPARATORS = ["_", "-", "H", "I", "J", "K", "L", "M", "N", "O", "P", 
                       "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"];
  var cbSep = CB_SEPARATORS[Math.floor(Math.random() * CB_SEPARATORS.length)];
  var cacheBreakerPrefix = ((new Date()).getTime() - CB_EPOCH).toString(16) + cbSep;
  var cacheBreakerSuffix = 0;
  
  /**
   * Generate a cache breaker to append to a URL.
   */
  function getCb() {
    var cb = cacheBreakerPrefix + cacheBreakerSuffix.toString(16);
    cacheBreakerSuffix++;
    return cb;
  }
  mod.getCb = getCb;
  
  /**
   * Does a deep copy of a JS object, as long as it's JSONable.
   */
  function copyJsonObject(obj) {
    return JSON.parse(JSON.stringify(obj));
  }
  
  // ---------------------------------------------------------------------------
  // onload
  // ---------------------------------------------------------------------------
  function putHistory(key, value) {
    try {
      jQuery.totalStorage(key, value);
    } catch (e) {
      log("Error storing " + key);
    }
  }
  mod.putHistory = putHistory;
  
  function getHistory(key) {
    try {
      return jQuery.totalStorage(key);
    } catch (e) {
      log("Error retrieving key");
      return null;
    } 
  }
  mod.getHistory = getHistory;
  
  //Bind a callback that executes when document.location.hash changes.
  $(window).bind( "hashchange", function(e) {
    var hash = jQuery.param.fragment();
    log("Hash changed to '" + hash + "'");
    var newLocation = "";
    if (hash) {
      newLocation = jQuery.bbq.getState(PARAM_LOCATION);
    }
    
    page = mod.pages[newLocation];
    var state = jQuery.bbq.getState();
    if (!page) {
      log("Page " + newLocation + " not found, using default.");
      page = mod.pages[""];
      if (!page) {
        log("Default page not found");
      }
    }
    if (page) {
      changePage(page, state);
    }
  });
  
  function rewriteUrls(selector) {
    log("Updating URLs");
    $(selector + " a").each(function(idx, a) {
      var url = a.href;
      log("Old url " + url);
      var hashIdx = url.indexOf("#");
      if (hashIdx >= 0) {
        var hash = url.substring(hashIdx+1, a.href.length);
        if (!hash) {
          return;
        }
        $(a).click(function() {
          return goToPage(mod.pages[hash], {});
        });
      }
    });
  }
  
  // Given a key -> value map, return a function which ignores its
  // first argument and applies the indicated subsitution to the
  // second, and returns the result.
  //
  // Replaces all occurrences of {KEY} with the subs["KEY"].
  function multiSubst(subs) {
    return function (i, v) {
      for (var k in subs) {
        v = v.replace('\{' + k + '}', subs[k])
        v = v.replace('\{%' + k + '}', encodeURIComponent(subs[k]))
      }
      return v;
    }
  }
  mod.multiSubst = multiSubst;
    
  $(window).load(function() {
    // Since the event is only triggered when the hash changes, we need
    // to trigger the event now, to handle the hash the page may have
    // loaded with.
    rewriteUrls("body");
    $(window).trigger("hashchange");
  });

  return mod;
})(clearwater || {}, jQuery);
