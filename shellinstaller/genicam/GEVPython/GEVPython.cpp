// *****************************************************************************
//
// Copyright (c) 2018, Pleora Technologies Inc., All rights reserved.
//
// *****************************************************************************

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/numpyconfig.h>
#include <numpy/arrayobject.h>


#include <PvSampleUtils.h>
#include <PvSoftDeviceGEV.h>
#include <PvBuffer.h>
#include <PvFPSStabilizer.h>
#include <PvSampleTransmitterConfig.h>
#include <PvStreamingChannelSourceDefault.h>

#include "Defines.h"
#include "MyEventSink.h"
#include "MyRegisterEventSink.h"
#include "MySource.h"
#include "Utilities.h"

/******************************/
/* Important global variables */
/******************************/
u_int32_t sens_width = 640;
u_int32_t sens_height = 480;
u_int32_t sens_bpp = 32;
u_int32_t sens_live = 0;
u_int32_t sens_size = 0;
u_int8_t *sens_img = NULL;
float genicamgain = -1;
float genicamfps = -1;
float genicamexposuretime = -1;
PvString lInterface;
PvSoftDeviceGEV lDevice;
IPvSoftDeviceGEVInfo *lInfo;


/************************************************************/
/* Create Python interface                                  */
/************************************************************/
static PyObject *GEVPython_setparams(PyObject *self, PyObject *args);
static PyObject *GEVPython_getparams(PyObject *self, PyObject *args);
static PyObject *GEVPython_getremotecontrolledgain(PyObject *self, PyObject *args);
static PyObject *GEVPython_getremotecontrolledfps(PyObject *self, PyObject *args);
static PyObject *GEVPython_getremotecontrolledexposuretime(PyObject *self, PyObject *args);
static PyObject *GEVPython_run(PyObject *self, PyObject *args);
static PyObject *GEVPython_setip(PyObject *self, PyObject *args);
static PyObject *GEVPython_setimage(PyObject *self, PyObject *args);

static PyMethodDef GEVPythonMethods[] =
{
    { "setparams", GEVPython_setparams, METH_VARARGS, "set all sensor parameters before enabling the GEV engine" },
	{ "getparams", GEVPython_getparams, METH_VARARGS, "get all sensor parameters before enabling the GEV engine" },
    { "getremotecontrolledgain", GEVPython_getremotecontrolledgain, METH_VARARGS, "get gain settings propagated from genicam control" },
    { "getremotecontrolledfps", GEVPython_getremotecontrolledfps, METH_VARARGS, "get fps settings propagated from genicam control" },
    { "getremotecontrolledexposuretime", GEVPython_getremotecontrolledexposuretime, METH_VARARGS, "get exposure time settings propagated from genicam control" },
	{ "run", GEVPython_run, METH_VARARGS, "start/stop the GEV engine" },
	{ "setip", GEVPython_setip, METH_VARARGS, "set the according Ip address" },
	{ "setimage", GEVPython_setimage, METH_VARARGS, "set a new image" },
	{ NULL, NULL, 0, NULL }
};

static PyModuleDef GEVPythonModule = 
{
	PyModuleDef_HEAD_INIT,
	"GEVPython",
	"Creates a GigEVision Genicam camera device",
	-1,
	GEVPythonMethods
};


PyMODINIT_FUNC PyInit_GEVPython(void)
{
	return PyModule_Create(&GEVPythonModule);
}





PV_INIT_SIGNAL_HANDLER();


#define BUFFERCOUNT ( 16 )

void MyEventSink::OnCreateCustomRegisters( IPvSoftDeviceGEV *aDevice, IPvRegisterFactory *aFactory )
{
    PVUNREFPARAM( aDevice );

    //aFactory->AddRegister( "TestInt", 0x10000050, 4, PvGenAccessModeReadWrite, mRegisterEventSink );
    aFactory->AddRegister( "Analog Gain", 0x10000040, 4, PvGenAccessModeReadWrite, mRegisterEventSink );
    aFactory->AddRegister( "Frames Per Second", 0x10000044, 4, PvGenAccessModeReadWrite, mRegisterEventSink );
    aFactory->AddRegister( "Exposure Time", 0x10000048, 4, PvGenAccessModeReadWrite, mRegisterEventSink );

}

void MyEventSink::OnCreateCustomGenApiFeatures( IPvSoftDeviceGEV *aDevice, IPvGenApiFactory *aFactory )
{
    IPvRegisterMap *lMap = aDevice->GetRegisterMap();
    CreateSampleParameters( lMap, aFactory );
    //CreateChunkParameters( aFactory );
    //CreateEventParameters( aFactory );
}


void MyEventSink::CreateSampleParameters( IPvRegisterMap *aMap, IPvGenApiFactory *aFactory )
{
    /*printf("Starting Register Definitions");
    aFactory->SetName( "TestInt" );
    aFactory->SetDescription( "Int to test EventSink" );
    aFactory->SetToolTip( "TestInt" );
    aFactory->SetCategory( "Test Category" );
    aFactory->SetRepresentation( PvGenRepresentationLinear );
    aFactory->SetUnit( "Arbitrary Units" );
    aFactory->CreateInteger( aMap->GetRegisterByAddress( 0x10000050 ), 0, 100.0, 1 );
    */
    aFactory->SetName( "Analog Gain" );
    aFactory->SetDescription( "Analog Gain setting that is passed on to the Sensor" );
    aFactory->SetToolTip( "Only set values to 1, 2 or 4." );
    aFactory->SetCategory( "Remote Controllable Parameters" );
    aFactory->SetRepresentation( PvGenRepresentationPureNumber );
    aFactory->SetUnit( "dB" );
    aFactory->CreateFloat( aMap->GetRegisterByAddress( 0x10000040 ), 1, 4 );

    aFactory->SetName( "Frames Per Second" );
    aFactory->SetDescription( "FPS setting that is passed on to the Sensor" );
    aFactory->SetToolTip( "" );
    aFactory->SetCategory( "Remote Controllable Parameters" );
    aFactory->SetRepresentation( PvGenRepresentationPureNumber );
    aFactory->SetUnit( "" );
    aFactory->CreateFloat( aMap->GetRegisterByAddress( 0x10000044 ), 5, 30 );

    aFactory->SetName( "Exposure Time" );
    aFactory->SetDescription( "Exposure Time setting that is passed on to the Sensor" );
    aFactory->SetToolTip( "" );
    aFactory->SetCategory( "Remote Controllable Parameters" );
    aFactory->SetRepresentation( PvGenRepresentationPureNumber );
    aFactory->SetUnit( "" );
    aFactory->CreateFloat( aMap->GetRegisterByAddress( 0x10000048 ), 1, 10 );
}

void MyRegisterEventSink::PostWrite( IPvRegister *aRegister )
{
    
    if ( aRegister->GetAddress() == 0x10000040 )
    {
        
        aRegister->ReadFloat(genicamgain);        
        printf("Received Gain Value from Genicam: %f\n",genicamgain);

    }   else if ( aRegister->GetAddress() == 0x10000044 ) {

        aRegister->ReadFloat(genicamfps);        
        printf("Received FPS Value from Genicam: %f\n",genicamfps);

    } else if ( aRegister->GetAddress() == 0x10000048 ) {
        
        aRegister->ReadFloat(genicamexposuretime);        
        printf("Received Exposure Time Value from Genicam: %f\n",genicamexposuretime);

    }
       
    std::cout << aRegister->GetName().GetAscii() << " PostWrite" << std::endl;
}

MySource::MySource()
    : mWidth( 640 )
    , mHeight( 480 )
    , mPixelType( PvPixelMono8 )
    , mBufferCount( 0 )
    , mAcquisitionBuffer( NULL )
    , mSeed( 0 )
    , mFrameCount( 0 )
    , mChunkModeActive( false )
    , mChunkSampleEnabled( false )
{
}

MySource::~MySource()
{
}

void MySource::GetWidthInfo( uint32_t &aMin, uint32_t &aMax, uint32_t &aInc ) const
{
    aMin = WIDTH_MIN;
    aMax = WIDTH_MAX;
    aInc = WIDTH_INC;
}


///
/// \brief Height info query
///

void MySource::GetHeightInfo( uint32_t &aMin, uint32_t &aMax, uint32_t &aInc ) const
{
    aMin = HEIGHT_MIN;
    aMax = HEIGHT_MAX;
    aInc = HEIGHT_INC;
}

PvResult MySource::SetHeight( uint32_t aHeight )
{
    if ( ( aHeight < HEIGHT_MIN ) || ( aHeight > HEIGHT_MAX ) )
    {
        return PvResult::Code::INVALID_PARAMETER;
    }

    mHeight = aHeight;
    return PvResult::Code::OK;
}

PvResult MySource::SetPixelType( PvPixelType aPixelType )
{
    if ( ( aPixelType != PvPixelMono8 ) &&
        ( aPixelType != PvPixelMono16 ) )
    {
        return PvResult::Code::INVALID_PARAMETER;
    }

    mPixelType = aPixelType;
    return PvResult::Code::OK;
}

PvResult MySource::GetSupportedPixelType( int aIndex, PvPixelType &aPixelType ) const
{
    switch ( aIndex )
    {
    case 0:
        aPixelType = PvPixelMono8;
        return PvResult::Code::OK;

    case 1:
        aPixelType = PvPixelMono16;
        return PvResult::Code::OK;

    default:
        break;
    }

    return PvResult::Code::INVALID_PARAMETER;
}

PvResult MySource::SetWidth( uint32_t aWidth )
{
    if ( ( aWidth < WIDTH_MIN) || ( aWidth > WIDTH_MAX ) )
    {
        return PvResult::Code::INVALID_PARAMETER;
    }

    mWidth = aWidth;
    return PvResult::Code::OK;
}


///
/// \brief Chunk support
///

PvResult MySource::GetSupportedChunk( int aIndex, uint32_t &aID, PvString &aName ) const
{
    switch ( aIndex )
    {
    case 0:
        aID = CHUNKID;
        aName = "Sample";
        return PvResult::Code::OK;

    default:
        break;
    }

    return PvResult::Code::INVALID_PARAMETER;
}

PvResult MySource::GetSupportedRegion( int aIndex, uint32_t &aID, PvString &aName ) const
{
    PVUNREFPARAM( aIndex );
    PVUNREFPARAM( aID );
    PVUNREFPARAM( aName );

    return PvResult::Code::NOT_SUPPORTED;
}

bool MySource::GetChunkEnable( uint32_t aChunkID ) const
{
    switch ( aChunkID )
    {
    case CHUNKID:
        return mChunkSampleEnabled;

    default:
        break;
    }

    return false;
}

PvResult MySource::SetChunkEnable( uint32_t aChunkID, bool aEnabled )
{
    switch ( aChunkID )
    {
    case CHUNKID:
        mChunkSampleEnabled = aEnabled;
        return PvResult::Code::OK;

    default:
        break;
    }

    return PvResult::Code::INVALID_PARAMETER;
}

void MySource::OnOpen( const PvString &aDestIP, uint16_t aDestPort )
{
    std::cout << "Streaming channel opened to " << aDestIP.GetAscii() << ":" << aDestPort << std::endl;
}

void MySource::OnClose()
{
    std::cout << "Streaming channel closed" << std::endl;
}

void MySource::OnStreamingStart()
{
    std::cout << "Streaming start" << std::endl;
    mStabilizer.Reset();
}

void MySource::OnStreamingStop()
{
    std::cout << "Streaming stop" << std::endl;
}

PvBuffer *MySource::AllocBuffer()
{
    if ( mBufferCount < BUFFERCOUNT )
    {
        mBufferCount++;
        return new PvBuffer;
    }

    return NULL;
}

void MySource::FreeBuffer( PvBuffer *aBuffer )
{
    delete aBuffer;
    mBufferCount--;
}

PvResult MySource::QueueBuffer( PvBuffer *aBuffer )
{
    // We use mAcqusitionBuffer as a 1-deep acquisition pipeline
    if ( mAcquisitionBuffer == NULL )
    {
        // No buffer queued, accept it
        mAcquisitionBuffer = aBuffer;

        // Acquire buffer - could be done in another thread
        ResizeBufferIfNeeded( mAcquisitionBuffer );
        switch ( GetPixelType() )
        {
        case PvPixelMono8:
            FillTestPatternMono8( mAcquisitionBuffer );
            break;

        case PvPixelMono16:
            FillTestPatternMono16( mAcquisitionBuffer );
            break;

        default:
            break;
        }
        AddChunkSample( mAcquisitionBuffer );
        mFrameCount++;

        return PvResult::Code::OK;
    }

    // We already have a buffer queued for acquisition
    return PvResult::Code::BUSY;
}

PvResult MySource::RetrieveBuffer( PvBuffer **aBuffer )
{
    if ( mAcquisitionBuffer == NULL )
    {
        // No buffer queued for acquisition
        return PvResult::Code::NO_AVAILABLE_DATA;
    }

    while ( !mStabilizer.IsTimeToDisplay( DEFAULT_FPS ) )
    {
        PvSleepMs( 1 );
    }

    // Remove buffer from 1-deep pipeline
    *aBuffer = mAcquisitionBuffer;
    mAcquisitionBuffer = NULL;

    return PvResult::Code::OK;
}

void MySource::AbortQueuedBuffers()
{
}

uint32_t MySource::GetRequiredChunkSize() const
{
    return ( mChunkModeActive && mChunkSampleEnabled ) ? CHUNKSIZE : 0;
}

void MySource::ResizeBufferIfNeeded( PvBuffer *aBuffer )
{
    uint32_t lRequiredChunkSize = GetRequiredChunkSize();
    PvImage *lImage = aBuffer->GetImage();
    if ( ( lImage->GetWidth() != mWidth ) ||
         ( lImage->GetHeight() != mHeight ) ||
         ( lImage->GetPixelType() != mPixelType ) ||
         ( lImage->GetMaximumChunkLength() != lRequiredChunkSize ) )
    {
        lImage->Alloc( mWidth, mHeight, mPixelType, 0, 0, lRequiredChunkSize );
    }
}

void MySource::FillTestPatternMono8( PvBuffer *aBuffer )
{
    PvImage *lImage = aBuffer->GetImage();
    uint32_t lHeight = lImage->GetHeight();
    uint32_t lWidth = lImage->GetWidth();
	uint8_t *imagebuf = aBuffer->GetDataPointer();
	u_int32_t isize = lHeight * lWidth * 1;
	u_int32_t memsize = 0;
	if (isize > sens_size) {
		memsize = sens_size;
	} else {
		memsize = isize;
	}
	memcpy(imagebuf, sens_img, memsize);
}


void MySource::FillTestPatternMono16( PvBuffer *aBuffer )
{
    PvImage *lImage = aBuffer->GetImage();
    uint32_t lHeight = lImage->GetHeight();
    uint32_t lWidth = lImage->GetWidth();
	uint8_t *imagebuf = aBuffer->GetDataPointer();
	u_int32_t isize = lHeight * lWidth * 2;
	u_int32_t memsize = 0;
	if (isize > sens_size) {
		memsize = sens_size;
	} else {
		memsize = isize;
	}
	memcpy(imagebuf, sens_img, memsize);
}

void MySource::AddChunkSample( PvBuffer *aBuffer )
{
    if ( !mChunkModeActive || !mChunkSampleEnabled )
    {
        return;
    }

    // Add frame count to chunk data
    uint8_t lData[ 36 ] = { 0 };

    // Add frame count to chunk data
    memcpy( lData, &mFrameCount, sizeof( mFrameCount ) );

    // Add current time string to chunk data
    Time2UInt8( lData + 4, sizeof( lData ) - 4 );

    // Add chunk data to buffer
    aBuffer->ResetChunks();
    aBuffer->SetChunkLayoutID( CHUNKLAYOUTID );
    aBuffer->AddChunk( CHUNKID, lData, sizeof( lData ) );

}


MySource lSimpleSource;
// Instantiate interface implementations
MyRegisterEventSink lRegisterEventSink;
MyEventSink lEventSink( &lRegisterEventSink );

/************************************************************/
/* Implement Python Methods                                 */
/************************************************************/
static PyObject *GEVPython_setparams(PyObject *self, PyObject *args) {
        PyObject *result = NULL;

        if(!PyArg_ParseTuple(args, "iii", &sens_width, &sens_height, &sens_bpp)) {
		PyErr_SetString(PyExc_ValueError, "Data parsing failed");
                return NULL;
        }
	if(sens_img != NULL) {
		free(sens_img);
	}
    if (sens_bpp == 8) {
	    sens_size = sens_width * sens_height * 1;
    } else {
        sens_size = sens_width * sens_height * 2;
    }
	sens_img = (u_int8_t*)malloc(sens_size);

	result = Py_BuildValue("i", 0);

        return result;
}

static PyObject *GEVPython_getparams(PyObject *self, PyObject *args) {
        PyObject *result = NULL;

        result = Py_BuildValue("(iii)", sens_width, sens_height, sens_bpp);


        return result;
}

static PyObject *GEVPython_getremotecontrolledgain(PyObject *self, PyObject *args) {
        PyObject *result = NULL;

        result = Py_BuildValue("f", genicamgain);


        return result;
}

static PyObject *GEVPython_getremotecontrolledfps(PyObject *self, PyObject *args) {
        PyObject *result = NULL;

        result = Py_BuildValue("f", genicamfps);


        return result;
}

static PyObject *GEVPython_getremotecontrolledexposuretime(PyObject *self, PyObject *args) {
        PyObject *result = NULL;

        result = Py_BuildValue("f", genicamexposuretime);


        return result;
}

static PyObject *GEVPython_setip(PyObject *self, PyObject *args) {
	PyObject *result = NULL;
	char *ip;
	if(!PyArg_ParseTuple(args, "s", &ip)) {
		PyErr_SetString(PyExc_ValueError, "Data parsing failed");
		return NULL;
	}
	printf("SET ip address: %s\n", ip);
	lInterface = PvString(ip);
	result = Py_BuildValue("s", ip);
	return result;

}

static PyObject *GEVPython_setimage(PyObject *self, PyObject *args) {
	PyObject *result = NULL;
	PyObject *input;
//	PyObject *inarr;
	u_int8_t *img;

	if(!PyArg_ParseTuple(args, "O", &input)) {
		PyErr_SetString(PyExc_ValueError, "Data parsing failed");
	}
//	inarr = PyArray_FROM_OTF(input, NPY_UBYTE, NPY_ARRAY_IN_ARRAY);
//	if (inarr == NULL) {
//		PyErr_SetString(PyExc_ValueError, "No ndarray");
//		return NULL;
//	}


//	img = (u_int8_t*)PyArray_DATA((PyArrayObject *)input);
	img = (u_int8_t*)PyArray_BYTES((PyArrayObject *)input);
	memcpy(sens_img, img, sens_size);
//	Py_DECREF(inarr);
 
	result = Py_BuildValue("i", 0);
	return result;
}

static PyObject *GEVPython_run(PyObject *self, PyObject *args) {
        PyObject *result = NULL;
        u_int32_t onoff = 0;
        if(!PyArg_ParseTuple(args, "i", &onoff)) {
		PyErr_SetString(PyExc_ValueError, "data parsing failed");
                return NULL;
        }
	printf("RUN executed\n");
	if((onoff > 0) && (sens_live == 0)) {
        printf("Starting Stream.\n");
		sens_live = 1;
    		if ( lInterface.GetLength() == 0 )
    			{
				PyErr_SetString(PyExc_ValueError, "No interface selected");
        			std::cout << "No interface selected, terminating" << std::endl;
        			return NULL;
    			}
    		lDevice.AddStream( &lSimpleSource );
            printf("Registering Event Sink");
            lDevice.RegisterEventSink( &lEventSink );
            
//    		*lInfo = lDevice.GetInfo();
	    	PvResult lResult = lDevice.Start( lInterface );
    		if ( !lResult.IsOK() )
    		{
			PyErr_SetString(PyExc_ValueError, "Unable to start streaming");
        		std::cout << "Error starting " << std::endl;
        		return NULL;
    		}

	} else if ((onoff > 0) && (sens_live == 1))  {
        printf("Resuming Stream.\n");
        PvResult lResult = lDevice.Start( lInterface );
    		if ( !lResult.IsOK() )
    		{
			PyErr_SetString(PyExc_ValueError, "Unable to start streaming");
        		std::cout << "Error starting " << std::endl;
        		return NULL;
    		}
    } else if(sens_live == 1) {
            sens_live = 0;
            printf("Stopping Stream.\n");
    		lDevice.Stop();

	}

	result = Py_BuildValue("i", onoff);
        return result;
}


/*
    PvFlushKeyboard();
    while ( !PvKbHit() )
    {
        PvSleepMs( 100 );
    }
*/
