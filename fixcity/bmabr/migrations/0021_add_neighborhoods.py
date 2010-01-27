
from south.db import db
from django.db import models
from fixcity.bmabr.models import *
import os

HERE = os.path.abspath(os.path.dirname(__file__))

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Neighborhood'
        db.start_transaction()
        db.create_table(u'gis_neighborhoods', (
            ('gid', orm['bmabr.neighborhood:gid']),
            ('objectid', orm['bmabr.neighborhood:objectid']),
            ('name', orm['bmabr.neighborhood:name']),
            ('state', orm['bmabr.neighborhood:state']),
            ('stacked', orm['bmabr.neighborhood:stacked']),
            ('annoline1', orm['bmabr.neighborhood:annoline1']),
            ('annoline2', orm['bmabr.neighborhood:annoline2']),
            ('annoline3', orm['bmabr.neighborhood:annoline3']),
            ('annoangle', orm['bmabr.neighborhood:annoangle']),
            ('borough', orm['bmabr.neighborhood:borough']),
            ('the_geom', orm['bmabr.neighborhood:the_geom']),

        ))
        db.send_create_signal('bmabr', ['Neighborhood'])

        db.commit_transaction()

        db.start_transaction()
        db.execute_deferred_sql()  # This is needed to set up the_geom.
        db.commit_transaction()

        # Now we can populate the table.
        db.start_transaction()
        sql_path = os.path.abspath(
            os.path.join(HERE, '..', '..', 'sql', 'gis_neighborhoods.sql'))
        db.execute_many(open(sql_path).read())
        db.commit_transaction()

    def backwards(self, orm):
        
        # Deleting model 'Neighborhood'
        db.delete_table(u'gis_neighborhoods')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'bmabr.borough': {
            'Meta': {'db_table': "u'gis_boroughs'"},
            'borocode': ('django.db.models.fields.SmallIntegerField', [], {}),
            'boroname': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'gid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'shape_area': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'shape_leng': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'the_geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {})
        },
        'bmabr.cityrack': {
            'Meta': {'db_table': "u'gis_cityracks'"},
            'address': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'alt_addres': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'boro_1': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'borocode': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'c_racksid': ('django.db.models.fields.CharField', [], {'max_length': '17'}),
            'from__cros': ('django.db.models.fields.CharField', [], {'max_length': '22'}),
            'gid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '13'}),
            'large': ('django.db.models.fields.IntegerField', [], {}),
            'neighborho': ('django.db.models.fields.CharField', [], {'max_length': '21'}),
            'objectid': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'oppaddress': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'rackid': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'side_of_st': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'small': ('django.db.models.fields.IntegerField', [], {}),
            'street_nam': ('django.db.models.fields.CharField', [], {'max_length': '31'}),
            'the_geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'to__cross': ('django.db.models.fields.CharField', [], {'max_length': '22'}),
            'x': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'y': ('django.db.models.fields.DecimalField', [], {'max_digits': '1000', 'decimal_places': '100'}),
            'zip_code_1': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        },
        'bmabr.communityboard': {
            'Meta': {'db_table': "u'gis_community_board'"},
            'board': ('django.db.models.fields.IntegerField', [], {}),
            'borocd': ('django.db.models.fields.IntegerField', [], {}),
            'borough': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bmabr.Borough']"}),
            'gid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'the_geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {})
        },
        'bmabr.emailsource': {
            'address': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'source_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bmabr.Source']", 'unique': 'True', 'primary_key': 'True'})
        },
        'bmabr.neighborhood': {
            'Meta': {'db_table': "u'gis_neighborhoods'"},
            'gid': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'}),

            'objectid': ('django.db.models.fields.IntegerField', [], {}),
            'stacked': ('django.db.models.fields.IntegerField', [], {}),
            'annoline1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'annoline2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'annoline3': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'annoangle': ('django.db.models.fields.DecimalField', [], {'max_digits': '100', 'decimal_places': '20'}),
            'borough': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'the_geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
        },
        'bmabr.nycdotbulkorder': {
            'communityboard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bmabr.CommunityBoard']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'bmabr.nycstreet': {
            'Meta': {'db_table': "u'gis_nycstreets'"},
            'gid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'nodeidfrom': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'nodeidto': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'the_geom': ('django.contrib.gis.db.models.fields.MultiLineStringField', [], {}),
            'zipleft': ('django.db.models.fields.CharField', [], {'max_length': '5'})
        },
        'bmabr.rack': {
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bmabr.Source']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'bmabr.seeclickfixsource': {
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'issue_id': ('django.db.models.fields.IntegerField', [], {}),
            'reporter': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bmabr.Source']", 'unique': 'True', 'primary_key': 'True'})
        },
        'bmabr.source': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'bmabr.statementofsupport': {
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            's_rack': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bmabr.Rack']"})
        },
        'bmabr.twittersource': {
            'source_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bmabr.Source']", 'unique': 'True', 'primary_key': 'True'}),
            'status_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }
    
    complete_apps = ['bmabr']
