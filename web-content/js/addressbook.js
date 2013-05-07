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
