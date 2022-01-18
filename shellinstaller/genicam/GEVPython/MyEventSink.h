// *****************************************************************************
//
// Copyright (c) 2018, Pleora Technologies Inc., All rights reserved.
//
// *****************************************************************************

#pragma once

#include <PvSoftDeviceGEVInterfaces.h>


///
/// \brief Software GigE Vision Device general event sink
///

class MyEventSink
    : public IPvSoftDeviceGEVEventSink
{
public:

    MyEventSink( IPvRegisterEventSink *aRegisterEventSink );
    virtual ~MyEventSink();

    // IPvSoftDeviceGEVEventSink implementation
    
    void OnCreateCustomRegisters( IPvSoftDeviceGEV *aDevice, IPvRegisterFactory *aFactory );
    void OnCreateCustomGenApiFeatures( IPvSoftDeviceGEV *aDevice, IPvGenApiFactory *aFactory );

protected:

    void CreateSampleParameters( IPvRegisterMap *aMap, IPvGenApiFactory *aFactory );
    





private:

    IPvRegisterEventSink *mRegisterEventSink;

};

