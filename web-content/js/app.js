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
  var log = mod.log;

  if(!$.cookie("username"))
  {
    log("Do not have cookie, redirect to login page");
    window.location.href = "/login.html";
    return;
  }

  var parsedUrl = mod.parseUrl();
  var username = null;
  var full_name = null;
  if (parsedUrl["params"]["data"]) {
    log(parsedUrl["params"]["data"]);
    var data = JSON.parse(parsedUrl["params"]["data"]);
    username = data["username"];
    full_name = data["full_name"];
    jQuery.totalStorage("username", username);
    jQuery.totalStorage("full_name", full_name);
  }

  if (!username) {
    username = jQuery.totalStorage("username");
  }
  if (!full_name) {
    full_name = jQuery.totalStorage("full_name");
  }
  var accUrlPrefix = "/accounts/" + encodeURIComponent(username);
  var numbersUrl = accUrlPrefix + "/numbers/";

  var knownPasswords = {};

  // To make sure the DOM has settled, wrap in ready() function
  // Put any calls that rely on the DOM being ready in here
  $(function() {
    $("#logout-button").click(function() {
      log("Logging out user");
      $.cookie("username", null);
      window.location.href = "/login.html";
      });
  });


  var dashboardPage = new mod.Page("dashboard", "#dashboard");

  dashboardPage.restoreState = function(state) {
    this.getHttp(accUrlPrefix + "/numbers/", {})
      .done(dashboardPage.populateTemplate)
      .fail(function() {
        log("Failed to retrieve numbers.");
        $("#numbers-error").show();
      });

    var handler = dashboardPage.numberCreator();
    $("#create-number-button").click(handler);
    $("#create-number-dropdown li").click(handler);
  };

  // Given a private id, generates a function for creating numbers associated
  // with that id. For unassociated numbers, do not pass in a private id
  dashboardPage.numberCreator = function(privateId) {
    return function(e) {
      var pstn = $(this).data("pstn");
      log("Creating a number");
      var data = {'pstn': pstn};
      if (privateId) {
        data["private_id"] = privateId;
      }
      dashboardPage.postHttp(numbersUrl, data)
        .done(dashboardPage.onNumberCreated);
    }
  };

  dashboardPage.onNumberDeleted = function(data) {
    // Just refresh the page.
    mod.goToPage(dashboardPage);
  };

  dashboardPage.onNumberCreated = function(data) {
    if (data["sip_password"] != undefined) {
      knownPasswords[data["private_id"]] = data["sip_password"];
    }
    mod.goToPage(dashboardPage);
  };

  dashboardPage.populateTemplate = function(data) {
    // Extract templates from HTML, sigh
    var templateRow = $("#template-number-list-row");
    var publicIdRow = $("#template-public-id");
    var tbody = templateRow.parent();
    templateRow.remove();
    templateRow.removeClass("template");
    publicIdRow.remove();
    publicIdRow.removeClass("template");
    var numbers = data["numbers"];

    // Group numbers by private id
    var grouped = {};
    for (var n in numbers) {
      var privateId = numbers[n]["private_id"];
      if (privateId === undefined) {
        log("Number did not have a private id associated");
        break;
      }
      if (grouped[privateId] === undefined) {
        grouped[privateId] = [];
      }
      grouped[privateId].push(numbers[n]);
    }

    var sortedPrivateIds = Object.keys(grouped).sort();
    for (var privateId in sortedPrivateIds) {
      (function(privateId, numberGroup) {
        var clone = templateRow.clone();
        var number = grouped[privateId][0];
        // First setup UI associated with the private id
        log("Adding cell for private id " + privateId);
        $(clone).find(".private-id").text(privateId);
        if (knownPasswords[number["private_id"]]) {
          $(clone).find(".password").text(knownPasswords[number["private_id"]]);
          $(clone).find(".password").show();
          $(clone).find(".password-tip").show();
          $(clone).find(".password-unavailable").hide();
        }
        $(clone).find(".reset-password-button").click(function() {
          if (confirm("Are you sure you want to reset the password for this number?")) {
            log("Resetting password for " + number["formatted_number"]);
            dashboardPage.postHttp(accUrlPrefix + "/numbers/" +
                          encodeURIComponent(number["sip_uri"]) + "/password",
                          {})
              .done(function(data) {
                knownPasswords[number["private_id"]] = data["sip_password"];
                mod.goToPage(dashboardPage);
              });
          }
        });

        // Now spin through all the numbers, adding the UI for each
        for (var n in numberGroup) {
          (function(number) {
            log("Adding cell for public id " + number);
            var publicIdListContainer = $(clone).find(".public-id-list");
            var publicIdRowClone = publicIdRow.clone();

            $(publicIdRowClone).find(".sip-uri").text(number["sip_uri"]);

            var pstn_badge = $(publicIdRowClone).find(".pstn-badge");
            if (number['pstn']) {
              $(pstn_badge).show();
            } else {
              $(pstn_badge).hide();
            }

            $(publicIdRowClone).find(".delete-button").click(function() {
              if (confirm("Are you sure you want to delete this number?")) {
                log("Resetting password for " + number["formatted_number"]);
                dashboardPage.deleteHttp(accUrlPrefix + "/numbers/" +
                                          encodeURIComponent(number["sip_uri"]))
                  .done(dashboardPage.onNumberDeleted);
              }
            });
            $(publicIdRowClone).find(".configure-button").click(function() {
              function displayConfigure(simservsData, gabData, iFCData){
                dashboardPage.populateConfigureModal(number["sip_uri"],
                                                     $.parseXML(simservsData[0]),
                                                     gabData[0]["gab_listed"],
                                                     $.parseXML(iFCData[0]));
              }

              var simservsGet = dashboardPage.getHttp(accUrlPrefix + "/numbers/" +
                                                      encodeURIComponent(number["sip_uri"]) + "/simservs",
                                                      {});
              var gabGet = dashboardPage.getHttp(accUrlPrefix + "/numbers/" +
                                                      encodeURIComponent(number["sip_uri"]) + "/listed",
                                                      {});
              var iFCGet = dashboardPage.getHttp(accUrlPrefix + "/numbers/" +
                                                      encodeURIComponent(number["sip_uri"]) + "/ifcs",
                                                      {});
              // Fetch data in parallel, launching modal when all requests complete
              $.when(simservsGet, gabGet, iFCGet)
                .done(displayConfigure)
                .fail(function() {
                  log("Failed to retrieve configuration from server.");
                });
            });

            publicIdListContainer.append(publicIdRowClone);
          })(numberGroup[n]);
        }

        if (numberGroup.length >= 5) {
          // Limit to creating 5 public ids
          $(clone).find(".button-bar").hide();
        }

        var handler = dashboardPage.numberCreator(privateId);
        $(clone).find(".add-public-id-btn").click(handler);
        $(clone).find(".add-public-id-dropdown li").click(handler);

        tbody.find("#add-private-id-row").before(clone);
      })(sortedPrivateIds[privateId], grouped[sortedPrivateIds[privateId]]);
    }
    if (numbers.length > 0) {
      $("#no-numbers").hide();
    } else {
      $("#no-numbers").show();
    }

    // Must initialize bootstrap hovertips explicitly
    $(".hovertip").tooltip();
  };

    dashboardPage.populateConfigureModal = function(sip_uri, xml, gabListed, iFCXML) {
    // We reuse the modal dialog, so be sure to cleanup when closing, see the cleanup() function below
    var configureModal = $("#configure-modal");
    var activeAppServers = []; //Populated when we create the checkboxes for the AS tab
    
    var saveConfiguration = function(){
      for (var i = 0; i < activeAppServers.length; i++) {
          var name = activeAppServers[i];
          $(iFCXML).find("ServiceProfile").append(allAppServers[name]);
      }
    
      var putSimservs = dashboardPage.putHttp(accUrlPrefix + "/numbers/" +
                                              encodeURIComponent(sip_uri) + "/simservs",
                                              new XMLSerializer().serializeToString(xml));
      var putiFCs = dashboardPage.putHttp(accUrlPrefix + "/numbers/" +
                                              encodeURIComponent(sip_uri) + "/ifcs",
                                              new XMLSerializer().serializeToString(iFCXML));
      var gabListed = gabCheckBox.is(':checked') ? 1 : 0;
      var putGab = dashboardPage.putHttp(accUrlPrefix + "/numbers/" +
                                         encodeURIComponent(sip_uri) + "/listed/" +
                                         gabListed + "/", {});

      $.when(putSimservs, putGab, putiFCs)
        .done(function(){
          log("Updated configuration on server");
          configureModal.modal("hide");
        })
        .fail(function() {
          log("Failed to update configuration");
        });
    };

    // Bind action to put xml to save button
    configureModal.find("#save-configure-button").click(saveConfiguration);

    // Optimized XML filter function to use instead of jQuery find where
    // namespaces are involved.
    $.fn.filterNode = function(name) {
      return this.filter(function() {
        return this.nodeName === name;
      });
    };

    // Cross-browser working xml.createELement replacement
    // This is necessary in order to corretly work in both Chrome and Firefox. Firefox will automatically add
    // a namespace to an element if it is not specified, resulting in xmlns="" in added elements
    var makeXmlElement = function(nodeName) {
	var nameSpace = nodeName.slice(0, 3) == "cp:" ? "urn:ietf:params:xml:ns:common-policy" : "http://uri.etsi.org/ngn/params/xml/simservs/xcap";
        return xml.createElementNS(nameSpace, nodeName);
    };

    // Function to check xml has expected node, appending it if missing
    var addNodeIfMissing = function(nodeParent, nodeName, attributes, value) {
      if (nodeParent.length == 0) {
        log("Cannot add node " + nodeName + " as parent " + nodeParent+ " does not exist")
          return;
      }

      // If the node has a namespace, we must strip it off before searching, or the
      // search will fail
      //var strippedNodeName = nodeName.replace(/^.+:/, "");
      //if (nodeParent.find(strippedNodeName).length == 0 ) {
      if (nodeParent.find('*').filterNode(nodeName).length == 0) {
        var e = makeXmlElement(nodeName);
        if (attributes) {
          for (var a in attributes) {
           $(e).attr(a, attributes[a]);
          }
        }
        nodeParent.append(e);
        if (value) {
          //nodeParent.find(nodeName).text(value);
          nodeParent.find('*').filterNode(nodeName).text(value);
        }
      }
    }

    var XMLcontains = function(container, contained) {
        var container_str = new XMLSerializer().serializeToString(container);
        var contained_str = new XMLSerializer().serializeToString(contained);
        return (container_str.indexOf(contained_str) != -1);
   }

    var removeFromXML = function(xml, node) {
        $(xml).find('InitialFilterCriteria').filter(function() {return new XMLSerializer().serializeToString(this) == new XMLSerializer().serializeToString(node)}).remove()
    }
    
    // Privacy
    // Connect caller ID checkbox to XML attribute
    var callerIdCheckBox = configureModal.find("#callerIdCheckBox");
    var callerIdXml = $(xml).find('originating-identity-presentation-restriction');
    var callerIdDefaultXml = callerIdXml.find('default-behaviour');
    var callerIdEnabled = callerIdXml.attr("active") == "true" &&
                          callerIdDefaultXml.text() == "presentation-not-restricted";
    callerIdCheckBox.prop("checked", callerIdEnabled);
    callerIdCheckBox.click(function(){
      // Always enable OIR service
      callerIdXml.attr("active", "true");
      // Set default to restricted if checkbox set, not restricted otherwise.
      callerIdDefaultXml.text(callerIdCheckBox.prop("checked") ?
                    "presentation-not-restricted" : "presentation-restricted");
    });

    // GAB availability
    var gabCheckBox = configureModal.find("#gabCheckBox");
    gabCheckBox.prop("checked", gabListed);

    // Redirect
    addNodeIfMissing($(xml).find('simservs'), 'communication-diversion', {'active': 'false'});
    var callDiversionXml = $(xml).find('communication-diversion');

    // Connect call diversion checkbox to XML attribute
    var callDiversionCheckBox = configureModal.find("#callDiversionCheckBox");
    var callDiversionEnabled = callDiversionXml.attr("active") == "true";
    callDiversionCheckBox.prop("checked", callDiversionEnabled);
    callDiversionCheckBox.click(function(){
      callDiversionXml.attr("active", callDiversionCheckBox.prop("checked"));
      if (callDiversionCheckBox.prop("checked")) {
        configureModal.find(".redirect-rule-inactive").hide();
      }
      else {
        configureModal.find(".redirect-rule-inactive").show();
      }
    });

    // Connect no-reply-timer dropdown to XML attribute
    addNodeIfMissing(callDiversionXml, 'NoReplyTimer', {}, '20');
    var noReplyTimerDropdown = configureModal.find("#no-reply-timer-dropdown");
    var noReplyTimer = callDiversionXml.find('NoReplyTimer').text();

    // Get user friendly names for timeouts
    var timeoutDescriptions = {};
    noReplyTimerDropdown.find("li").each(function(i, element){
      timeoutDescriptions[$(element).data("timer")] = $(element).find("a").text();
    });
    configureModal.find("#no-reply-timer-value").text(timeoutDescriptions[noReplyTimer] || noReplyTimer + " seconds ");
    noReplyTimerDropdown.find("li:not(.disabled)").each(function(i, timerElement){
      $(timerElement).click(function(){
        var timer = $(timerElement).data("timer");
        configureModal.find("#no-reply-timer-value").text(timeoutDescriptions[timer] || timer + " seconds ");
        callDiversionXml.find('NoReplyTimer').text(timer);
      });
    });

    var rulesAccordion = configureModal.find("#rules-accordion");
    var templateRule = rulesAccordion.find(".redirect-rule.template");

    // Helper function for adding a rule
    var addRule = function(i, ruleXml)
    {
      // Clone from template to create new rule
      var rule = templateRule.clone();
      rule.removeClass("template");

      // Hook up href between heading and body - cannot just use the id in the template
      rule.find(".accordion-heading a.accordion-toggle").attr('href', '#rule' + i);
      rule.find(".accordion-body").attr('id', 'rule' + i);
      rule.hide();
      rulesAccordion.append(rule);
      rule.show('fast');

      var callDiversionEnabled = configureModal.find("#callDiversionCheckBox").prop("checked");
      if (callDiversionEnabled) {
        rule.find(".redirect-rule-inactive").hide();
      }

      // We want to overflow the rule body so the dropdown doesn't get cut off. However, we cannot
      // do that until the body has animated in, which is why we use the setTimeout below
      rule.find(".rule-title").on('click', function(){
        rulesAccordion.find(".accordion-body").each(function(i, ruleBody){
          $(ruleBody).removeClass('rule-overflow');
        });

        // The accordion component uses the 'in' class to determin if a section is open
        if (!rule.find(".accordion-body").hasClass('in')) {
          setTimeout(function(){ rule.find(".accordion-body").addClass('rule-overflow')}, 500);
        }
      });

      var setRuleTitle = function(target)
      {
        var title = !target || target == "" ? "Empty rule" : "Rule for " + target;
        rule.find(".rule-title").text(title);;
      }

      // Connect the sip address for the redirection UI to XML
      var redirectTarget = rule.find(".redirect-target");
      var callDiversionEnabled = $(ruleXml).find('communication-diversion').attr("active") == "true";
      var currentTarget = $(ruleXml).find('target').text();
      redirectTarget.val(currentTarget);
      setRuleTitle(currentTarget);
      redirectTarget.change(function(){
        $(ruleXml).find('target').text(redirectTarget.val());
        setRuleTitle(redirectTarget.val());
      });

      // Get user friendly names for conditions
      var conditionDescriptions = {};
      rule.find(".add-condition-menu").find("li").each(function(i, element){
        conditionDescriptions[$(element).data("condition")] = $(element).find("a").text();
      });

      // Populate conditions with values in XML
      var redirectConditions = rule.find(".redirect-conditions");
      var templateCondition = redirectConditions.find(".template");

      // Helper function to add UI displaying a condition and binding that UI to the XML data
      var addCondition = function(xmlElement)
      {
        if (xmlElement.textContent != "") {
          // Some conditions come wrapped in a type, we only care about the condition
          var condition = xmlElement.textContent;
        }
        else {
          // Other conditions are not wrapped, so just pick out condition from node name
          var condition = xmlElement.nodeName;
        }

        // Remove this option from the dropdown menu as we already have this as part of the rule
        rule.find(".redirect-condition-dropdown li[data-condition='" + condition + "']").hide();

        // Clone from template to create new row for condition
        var clone = templateCondition.clone();
        clone.removeClass("template");
        $(clone).find(".redirect-condition-label").text(conditionDescriptions[condition]);
        $(clone).find(".redirect-condition-label").data("condition", condition);
        $(clone).find(".redirect-condition-remove").click(function(){
          var n = rule.find(".redirect-conditions .redirect-condition:not(.template)").length;
          if (n == 1) {
            // This is the last condition, so show the 'all calls' UI
            rule.find(".redirect-no-conditions").show('fast');
          }

          // Remove condition from XML and UI and show again in dropdown
          clone.hide('fast', function(){ clone.remove(); });
          $(xmlElement).remove();
          rule.find(".redirect-condition-dropdown li[data-condition='" + condition + "']").show();
        });

        // Fade in new condition and hide 'all calls' UI if showing
        $(clone).hide();
        redirectConditions.append(clone);
        $(clone).show('fast');

        // jQuery has a 'feature' where animated show/hide do not work if parent elements are hidden
        // For now, just stick with the non-animated version
        rule.find(".redirect-no-conditions").hide();
      }

      // Generate the UI for current rules from XML
      $(ruleXml).find('conditions').children().each(function(i, element){
        addCondition(element);
      });

      // Add click handler to 'new condition' menu that updates the UI along with the XML
      rule.find(".redirect-condition-dropdown li").each(function(i, conditionElement){
        $(conditionElement).click(function(){
          if ($(conditionElement).hasClass('disabled')) {
            return false;
          }
          var condition = $(conditionElement).data("condition");
          var type = $(conditionElement).data("type");

          // Note we need to create the new element on the existing xml document otherwise
          // jQuery will automatically add a default xmlns to it
          if(type != undefined) {
            // If we have a specific data type, wrap the condition in it. This is currently
            // just used for media conditions, but leaving as general for future expansion
            var element = makeXmlElement(type);
            $(element).text(condition);
          }
          else {
            var element = makeXmlElement(condition);
          }

          $(ruleXml).find('conditions').append(element);
          addCondition(element);
        });
      });

      // Click handler for deleting a rule
      rule.find(".redirect-rule-delete-button").click(function(){
          rule.hide('fast', function(){ rule.remove(); });
          $(ruleXml).remove();
          return false;
      });

      // It is not possible to have all conditions simultaneously, this function disable invalid options
      var disableInvalidConditions = function()
      {
        var enableCondition = function(condition, enable) {
          var conditionItem = rule.find(".redirect-condition-dropdown li[data-condition='" + condition + "']");
          if (enable) {
            conditionItem.removeClass('disabled');
          }
          else {
            conditionItem.addClass('disabled');
          }
        }

        // First enable all conditions, then disable depending on what conditions are already selected
        enableCondition("busy", true);
        enableCondition("no-answer", true);
        enableCondition("not-registered", true);
        enableCondition("not-reachable", true);
        rule.find(".redirect-condition-label").each(function(i, e){
          var condition = $(e).data("condition");
          if (condition == "not-registered" || condition == "not-reachable" ||
              condition == "busy" || condition == "no-answer") {
            enableCondition("busy", false);
            enableCondition("no-answer", false);
            enableCondition("not-registered", false);
            enableCondition("not-reachable", false);
          }
        });
      }

      rule.find(".dropdown-toggle").click(disableInvalidConditions);
    }; // addRule()

    // Iterate over all existing rules in xml and add in the UI
    callDiversionXml.find("rule").each(addRule);

    // Click handler for new rule button, creates new XML node and UI for rule
    configureModal.find("#redirect-new-rule-button").click(function(){
      addNodeIfMissing($(xml).find('communication-diversion'), 'cp:ruleset');

      // Pretty verbose, but taking shortcuts leads to jQuery adding a default xmlns
      var n = callDiversionXml.find('ruleset').children().length;
      var ruleElement = makeXmlElement("cp:rule");
      $(ruleElement).attr("id", "rule" + n);
      ruleElement.appendChild(makeXmlElement("cp:conditions"));
      var actionsElement = makeXmlElement("cp:actions");
      var forwardToElement = makeXmlElement("forward-to");
      forwardToElement.appendChild(makeXmlElement("target"));
      actionsElement.appendChild(forwardToElement);
      ruleElement.appendChild(actionsElement);
      callDiversionXml.find('ruleset').append(ruleElement);
      addRule(n, ruleElement);

      // As this is a new rule, open it for editing by invoking click handler
      rulesAccordion.find("#rule" + n).prev().find(".rule-title").click();

      return false;
    });

    // Barring
    var barringPane = configureModal.find("#barring-pane");
    var setupBarring = function(direction) {
      // Generate any needed XML if it is missing
      addNodeIfMissing($(xml).find('simservs'), direction + '-communication-barring', {'active': 'true'});
      var barXml = $(xml).find(direction + '-communication-barring');
      addNodeIfMissing(barXml, 'cp:ruleset');
      addNodeIfMissing(barXml.find('*').filterNode('cp:ruleset'), 'cp:rule', {'id': 'rule0'});
      addNodeIfMissing(barXml.find('*').filterNode('cp:rule'), 'cp:conditions');
      addNodeIfMissing(barXml.find('*').filterNode('cp:rule'), 'cp:actions');
      addNodeIfMissing(barXml.find('*').filterNode('cp:actions'), 'allow', {}, 'true');

      // Bind the UI to the XML
      var allow = barXml.find('allow').text();
      barringPane.find(".barring-radio[data-direction='" + direction + "'][data-allow='" + allow + "']").prop("checked", true);
      var condition = barXml.find('*').filterNode('cp:conditions').children()[0];
      if (condition) {
        barringPane.find(".barring-radio[data-direction='" + direction + "'][data-allow='" + allow + "'][data-condition='" + condition.nodeName + "']").prop("checked", true);
      }

      barringPane.find(".barring-radio[data-direction='" + direction + "']").click(function(){
        var radio = $(this);
        barXml.find('allow').text(radio.data("allow"));

        // The conditions element is currently only used for international barring
        var conditions = barXml.find('*').filterNode('cp:conditions');
        conditions.empty();
        if (radio.data("condition")) {
          conditions.append(makeXmlElement(radio.data("condition")));
        }
      });
    }

    setupBarring('incoming');
    setupBarring('outgoing');

    dashboardPage.populateASTemplate = function() {
	    var templateRow = configureModal.find(".as-row.template");
	    var tbody = templateRow.parent();

            // Build a list of names of all the app servers
	    var names = [];
	    for (var k in allAppServers) {
		    if (allAppServers.hasOwnProperty(k)) {
			    names.push(k);
		    }
	    }

	    // Loop through all possible ASes in the config file and create a checkbox for each
	    for (var i = 0; i < names.length; i++) {
		    (function(i) {
		     var clone = templateRow.clone();
		     clone.removeClass("template");
		     $(clone).find(".name").text(" " + names[i]);
		     var ASCheckBox = $(clone).find("#as-row");
		     // If this AS is already in the iFCs, pre-check this box
             var node = $.parseXML(allAppServers[names[i]]);
		     if (XMLcontains(iFCXML, node)) {
		     ASCheckBox.prop("checked", "true");
             activeAppServers.push(names[i]);
             removeFromXML(iFCXML, node)
		     } else {
		     ASCheckBox.removeProp("checked");
		     }
		     ASCheckBox.click(function(){
			     if (ASCheckBox.prop("checked")) {
			     activeAppServers.push(names[i]);
			     } else {
			     var index = activeAppServers.indexOf(names[i]);
                 activeAppServers.splice(index, 1);
			     }
			     });
		     tbody.append(clone);
		     })(i);
	    }

            // If we don't have any configured, show an informative message rather than a blank tab
	    if (names.length > 0) {
		    $("#no-as").hide();
	    } else {
		    $("#no-as").show();
	    }
    };

    dashboardPage.populateASTemplate();


    // As we reuse the same modal dialog we need to do some cleanup, eg unbind click handlers
    // so they don't get duplicated and any elements cloned from templates
    var cleanup = function(){
      configureModal.find("#save-configure-button").unbind("click");
      callerIdCheckBox.unbind("click");
      callDiversionCheckBox.unbind("click");
      configureModal.find("#redirect-new-rule-button").unbind("click");
      barringPane.find(".barring-radio").unbind("click");
      configureModal.find(".redirect-rule:not(.template)").remove();
      configureModal.find(".redirect-condition:not(.template)").remove();
      configureModal.find(".as-row:not(.template)").remove();
    };

    configureModal.on('hidden', function(){
      // 'hidden' can be triggered by other elements, so check the modal really has been hidden
      if (!configureModal.is(":visible")) {
        cleanup();
      }
    });

  }; // dashboardPage.populateConfigureModal()

  var hashValue = mod.parseUrl()["hash"];
  if (hashValue && hashValue.indexOf("first") != -1) {
    // First load after sign-up, so create a line before switching to the
    // dashboard page.
    log("Auto-create first line after sign-up");
    var url = location.href.toString().replace("first", "");
    dashboardPage.postHttp(numbersUrl, {})
      .done(function(data) {
        knownPasswords[data["private_id"]] = data["sip_password"];
        window.location.replace(url);
        mod.setDefaultPage(dashboardPage);
    });
  } else {
    // Normal load, so switch to the dashboard page.
    mod.setDefaultPage(dashboardPage);
  }

  return mod;
})(clearwater, jQuery);
