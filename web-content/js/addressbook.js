/**
 * Copyright (C) Metaswitch Networks
 * If license terms are provided to you in a COPYING file in the root directory
 * of the source code repository by which you are accessing this code, then
 * the license outlined in that COPYING file applies to your use.
 * Otherwise no rights are granted except for those provided to you by
 * Metaswitch Networks in a separate written agreement.
 */

var app = app || {};

$(function( $ ) {
  app.AppView = Backbone.View.extend({
    el: "#addressbook",

    events: {
      "keyup #search-addressbook": "search"
    },

    initialize: function () {
      var self = this;
      this.template = this.options.template;
      this.collection.fetch({
        success: function (collection, response) {
          var contacts = collection.at(0).get("contacts");
          self.render({"contacts": contacts});
        }
      });
    },

    render: function (contacts) {
      this.$el.find('#contact-list').html(this.template(contacts));
    },

    // Whenever the text in the search box changes, update the UI with filtered contacts
    search: function(e){
      this.render(this.collection.search($('#search-addressbook').val()));
    },
  });

  app.LogoutButton = Backbone.View.extend({
    el: "#logout-button",

    events: {"click": "logout"},

    logout: function() {
      $.cookie("username", null);
      window.location.href = "/login.html";
    },
  });

  // This represents the entire address book. As we only permit reading, there is no
  // need to worry about synchronization with the server, so we simply provide a url
  // to fetch from
  app.AddressBookCollection = Backbone.Collection.extend({
    url: '/gab',
    
    search : function(letters){
      var contacts = this.at(0).get("contacts");
      if(letters == "") {
        return {"contacts": contacts};
      }
       
      letters = letters.toLowerCase();
      var matches = function(s)
      {
        return s.toLowerCase().indexOf(letters) != -1;
      }
      var filtered = contacts.filter(function(data) {
          var testFields = [data["full_name"]];
          testFields = testFields.concat(data["numbers"]);
          return _.any(testFields, matches);
      });
      return {"contacts": filtered};
    },
  });

  app.loadTemplate = function(name, success){
    $.get('js/templates/' + name + '.html', success);
  };
});

$(function() {
  // First check if we're logged in
  if (!$.cookie("username")) {
    window.location.href = "/login.html";
    return;
  }
  // Initialize model, fetch template and start app
  var addressBookCollection = new app.AddressBookCollection();
  app.loadTemplate('addressbook-contacts', function(data) {
    new app.AppView({
      "collection": addressBookCollection,
      "template": _.template(data)
    });
    new app.LogoutButton();
  });
});
