#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torsearch import db
import stem

class Descriptor(db.Model):
  '''Corresponds to Stem's ServerDescriptor.

  Can be used both for RelayDescriptor and BridgeDescriptor.
  In the latter case, the fingerprint is actually a hashed fingerprint,
  the address is a kind of a hash of its IP address, etc., but the model
  is valid.
  '''

  __tablename__ = 'descriptor'

  NO_UNICODE = True # all these fields are ascii fields in the dir spec

  descriptor = db.Column(db.String(40), primary_key=True)
  fingerprint = db.Column(db.String(40), index=True)
  nickname = db.Column(db.String(19), index=True)
  published = db.Column(db.DateTime, index=True)
  address = db.Column(db.String(15), index=True)
  or_port = db.Column(db.Integer)
  dir_port = db.Column(db.Integer)
  platform = db.Column(db.String(256))
  #tor_version = db.Column(db.String(96)) # covered in platform (str version
  # OK for now)
  #operating_system = db.Column(db.String(256)) # covered in platform
  uptime = db.Column(db.BigInteger)
  contact = db.Column(db.LargeBinary) # some folks prefer to use l33t \x0's,
                                      # this is the safest way to store them
  exit_policy = db.Column(db.String) # stringified summary for now
  average_bandwidth = db.Column(db.BigInteger)
  burst_bandwidth  = db.Column(db.BigInteger)
  observed_bandwidth = db.Column(db.BigInteger)
  hibernating = db.Column(db.Boolean, server_default=db.text('FALSE'))
  extra_info_digest = db.Column(db.String(40))
  is_bridge = db.Column(db.Boolean, server_default=db.text('FALSE'))

  # fields that we can't simply copy from Stem's ServerDescriptor just like that:

  morphisms = {
    'descriptor': lambda stem_desc: stem_desc._path.split('/')[-1],
    'exit_policy': lambda stem_desc: stem_desc.exit_policy.summary(),
    'is_bridge': \
      lambda stem_desc: isinstance(stem_desc, stem.descriptor.server_descriptor.BridgeDescriptor)
  }

  def __init__(self, stem_desc=None):
    '''Will initialize itself with Stem's descriptor data, if passed
    '''

    if stem_desc:
      self.map_from_stem(stem_desc)

  def map_from_stem(self, stem_desc, onto=None):
    '''map Stem's ServerDescriptor onto self
    '''

    if not onto:
      onto = self
    for col in onto.__table__.columns:
      value = None
      if col.name in onto.morphisms:
        value = onto.morphisms[col.name](stem_desc)
      elif col.name in stem_desc.__dict__:
        value = stem_desc.__dict__[col.name]
      if value:
        if self.NO_UNICODE and isinstance(value, unicode):
          value = str(value) # this already assumes that the original value
                             # only contained ascii-encodable characters,
                             # so safe
        setattr(onto, col.name, value)

class Consensus(db.Model):
  '''Represents a network status document.

  Corresponds to NetworkStatusDocument
  '''

  __tablename__ = 'consensus'

  NO_UNICODE = True

  valid_after = db.Column(db.DateTime, primary_key=True)
  fresh_until = db.Column(db.DateTime)
  valid_until = db.Column(db.DateTime)

  def __init__(self, stem_doc = None):
    '''Will initialize itself with Stem's descriptor data, if passed
    '''

    if stem_doc:
      self.map_from_stem(stem_doc)

  def map_from_stem(self, stem_doc, onto=None):
    '''map Stem's NetworkStatusDocument onto self
    '''

    if not onto:
      onto = self
    for col in onto.__table__.columns:
      if col.name in stem_doc.__dict__:
        value = stem_doc.__dict__[col.name]
        if self.NO_UNICODE and isinstance(value, unicode):
          value = str(value) # this already assumes that the original value
                             # only contained ascii-encodable characters,
                             # so safe
        setattr(onto, col.name, value)

class StatusEntry(db.Model):
  '''A particular network status entry from a consensus document.

  Corresponds to RouterStatusEntry
  '''

  __tablename__ = 'statusentry'

  NO_UNICODE = True

  id = db.Column(db.Integer, primary_key=True)
  validafter = db.Column(db.DateTime, index=True)#, primary_key=True) # composite primary key (1/2)
  nickname = db.Column(db.String(19))
  fingerprint = db.Column(db.String(40))#, primary_key=True) # composite primary key (2/2)
  published = db.Column(db.DateTime, index=True)

  # TODO: proper column naming.
  # As of now, what we call a 40-char-length 'descriptor' is called
  # a 'digest'; that is how it is referred to
  # in dir-spec.txt, and how it appears in Stem's RouterStatusEntry.
  # Hence as of now, this column is empty.
  descriptor = db.Column(db.String(40), index=True)

  address = db.Column(db.String(15), index=True)
  or_port = db.Column(db.Integer)
  dir_port = db.Column(db.Integer)
  version_line = db.Column(db.String(96)) # ideally, we should also parse
                                          # 'version' and store its fields
                                          # preserving its semantics
  # RouterStatusEntryV3-specific fields

  # to quote dir-spec.txt, '"Digest" is a hash of its most recent descriptor as
  # signed (that is, not including the signature), encoded in base64.'
  digest = db.Column(db.String(40), index=True)

  bandwidth = db.Column(db.BigInteger)
  measured = db.Column(db.BigInteger)
  is_unmeasured = db.Column(db.Boolean)

  # and now the flags (for automatic mapping, we will
  # wickedly access __tables__ again directly, and look
  # for fields starting with 'is')
  # this does allow for some nice automated model mapping, and will need
  # minimal adjustments upon protocol / data format changes.

  isAuthority = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isBadExit = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isBadDirectory = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isExit = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isFast = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isGuard = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isHSDir = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isNamed = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isStable = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isRunning = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isUnnamed = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isValid = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isV2Dir = db.Column(db.Boolean, server_default=db.text('FALSE'))
  isV3Dir = db.Column(db.Boolean, server_default=db.text('FALSE'))

  morphisms = {}

  def __init__(self, stem_status=None, validafter=None):
    '''Will initialize itself with Stem's network status data, if passed
    '''

    if stem_status:
      self.map_from_stem(stem_status, validafter)

  def map_from_stem(self, stem_status, validafter, onto=None):
    '''map Stem's RouterStatusEntry onto self
    '''

    if not onto:
      onto = self
    onto.validafter = validafter
    for col in onto.__table__.columns:
      value = None
      if col.name in stem_status.__dict__:
        if col.name not in onto.morphisms:
          value = stem_status.__dict__[col.name]
        else:
          value = onto.morphisms[col.name](stem_status)
      elif col.name.startswith('is'): #and col.name[2:] in \
                                      #  map(str.lower, stem_status.flags):
        for flag in stem_status.flags: # is_measured will have been processed
                                       # before
          if flag.lower() == col.name[2:].lower(): # just in case
            setattr(onto, col.name, True)
      if value is not None:
        if self.NO_UNICODE and isinstance(value, unicode):
          value = str(value) # ditto re: we know it is ascii-encodable
        setattr(onto, col.name, value)

class Fingerprint(db.Model):
  '''A helper table which contains a unique fingerprint index.
  '''

  __tablename__ = 'fingerprint'

  FP_LEN = 40
  FP_SUBSTR_LEN = 12

  fp12 = db.Column(db.String(FP_SUBSTR_LEN), primary_key=True)
  fingerprint = db.Column(db.String(40))
  digest = db.Column(db.String(40))
  nickname = db.Column(db.String(19), index=True)
  address = db.Column(db.String(15))
  first_va = db.Column(db.DateTime)
  last_va = db.Column(db.DateTime)
  sid = db.Column(db.ForeignKey('statusentry.id'))


if __name__ == '__main__':
  pass
