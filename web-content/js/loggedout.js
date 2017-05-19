/**
 * Copyright (C) Metaswitch Networks
 * If license terms are provided to you in a COPYING file in the root directory
 * of the source code repository by which you are accessing this code, then
 * the license outlined in that COPYING file applies to your use.
 * Otherwise no rights are granted except for those provided to you by
 * Metaswitch Networks in a separate written agreement.
 */

var clearwater = (function(mod, $){ 
  var loginPage =new mod.Page("login", "#login");
  loginPage.restoreState = function() {
    mod.setFormAction("#login-form",
                      "/session",
                      "/index.html");
  };

  var signupPage = new mod.Page("signup", "#signup");
  signupPage.restoreState = function(state) {
    mod.setFormAction("#signup-form",
                      "/accounts",
                      "/index.html");
  };
  
  mod.setDefaultPage(loginPage);
  
  return mod;
})(clearwater, jQuery);
