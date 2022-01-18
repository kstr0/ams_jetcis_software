# Plot functions
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def profile(y, axis='', quantity='', unit=''):
    '''Plot the profile.

    Parameters
    ----------            
    y : np.array
        The profile

    axis : str
        Row or column for the x axis label

    quantity : str
        Parameter name for the y axis label

    unit : str
        Parameter unit for the y axis label
    '''
    stats_subtitle = f'mean {np.nanmean(y):.2f}, median {np.nanmedian(y):.2f}, stdv {np.nanstd(y):.2f}'

    fig = px.line(y=y, title=f'{axis} {quantity} <br><sup>{stats_subtitle}</sup>')
    fig.update_layout(
        xaxis_title=f'{axis} number',
        yaxis_title=f'{axis} {quantity} [{unit}]')
    fig.show()


def multi_profile(data, param, orientation):
    '''Plot the horizontal/vertical profiles.

    Parameters
    ----------            
    data : dict
        The profiles

    param : str
        The parameter name

    orientation : str
        Horizontal or Vertical
    '''
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in data.items()]))
    df.rename(columns={f'Index {orientation}': 'Index',
                    f'Min {orientation}':'Min', 
                    f'Middle {orientation}':'Middle',
                    f'Mean {orientation}':'Mean', 
                    f'Max {orientation}':'Max'}, 
            inplace=True)

    mean = np.mean(data[f'Mean {orientation}'])
    if orientation == 'Horizontal':
        fig = px.line(df, x='Index', y=['Max', 'Middle', 'Mean', 'Min'])
        fig.update_yaxes(range=[0.9 * mean, 1.1 * mean])
        fig.update_layout(xaxis_title='Index of the line',
                        yaxis_title='Vertical line [DN]',
                        title=f'{orientation} profile {param}',
                        legend={'title_text':''})
    else:
        fig = px.line(df, y='Index', x=['Max', 'Middle', 'Mean', 'Min'])
        fig.update_xaxes(range=[0.9 * mean, 1.1 * mean])
        fig.update_layout(yaxis_title='Index of the line',
                        xaxis_title='Vertical line [DN]',
                        title=f'{orientation} profile {param}',
                        legend={'title_text':''}, 
                        yaxis={'autorange':'reversed'})
    fig.show()


def histogram(data, hist, title='', unit='', nb_limit_std=10):
    '''Plot the histogram.

    Parameters
    ----------            
    data : np.array
        The image

    hist : dict
        Histogram bins and values

    title : str
        Additional title

    unit : str
        The unit in the x axis label
    
    nb_limit_std : int
        The amount of stds from the median for the x axis plot limits
    '''
    mean = np.nanmean(data)
    median = np.nanmedian(data)
    std = np.nanstd(data)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist['bins'], y=hist['values'],
                            mode='lines',
                            name='Data',
                            fill='tozeroy'))
    fig.add_trace(go.Scatter(x=hist['bins'], y=hist['model'],
                            mode='lines',
                            name='Model normal distribution', 
                            line=dict(dash='dot')))

    fig.update_xaxes(range=[- nb_limit_std * std, nb_limit_std * std])

    fig.update_yaxes(range=[0.5, np.log10(np.max(hist['values']) * 2)])
    fig.update_yaxes(type="log")

    fig.update_layout(
            xaxis_title=f'Deviation from mean [{unit}]',
            yaxis_title='Number of pixels/bin',
            title = f'Logarithmic histogram {title} <br><sup>mean {mean:.2f}, median {median:.2f}, stdv {std:.2f}</sup>')
    fig.show()


def accumulated_histogram(data, hist, title='', unit='', nb_limit_std=10):
    '''Plot the accumulated histogram.

    Parameters
    ----------            
    data : np.array
        The image

    hist : dict
        Histogram bins and values

    title : str
        Additional title

    unit : str
        The unit in the x axis label
    
    nb_limit_std : int
        The amount of stds from the median for the x axis plot limits
    '''
    std = np.nanstd(data)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist['accumulated bins'], y=hist['accumulated values'], mode='lines'))

    ulimit = nb_limit_std * std
    fig.update_xaxes(range=[0, ulimit])

    fig.update_yaxes(range=[np.log10(0.001), np.log10(100)])
    fig.update_yaxes(type="log")

    fig.update_layout(
            xaxis_title=f'Deviation from mean [{unit}]',
            yaxis_title='Percentage of pixels/bin',
            title = f'Accumulated logarithmic histogram {title}')
    fig.show()


def rowcolumn(data, llimit, ulimit, title=''):
    '''Plot the data.

    Parameters
    ----------            
    data : np.array
        The image

    llimit: float
        Lower limit of the data range
        
    ulimit : float
        Upper limit of the data range

    title : str
        Additional title
    '''
    fig = px.imshow(data, binary_string=True, color_continuous_scale='Viridis', 
                    title=title, 
                    labels={'x': 'Column', 'y':'Row'}, 
                    zmin=llimit, 
                    zmax=ulimit)
    # fig.update_traces(hovertemplate="Col: %{x} <br>Row: %{y} <br>Value: %{z[0]} <extra></extra>")
    fig.show()


def spectrogram(spect, param, paramstr):
    '''Plot the spectrogram.

    Parameters
    ----------            
    spect : dict
        The spectrogram

    param: float
        The parameter value
        
    paramstr : str
        The parameter name
    '''
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spect['horizontal cycles [periods/pixel]'],
                            y=spect['horizontal power spectrum'], 
                            mode='lines', 
                            name='Horizontal'))
    fig.add_trace(go.Scatter(x=spect['vertical cycles [periods/pixel]'], 
                            y=spect['vertical power spectrum'], 
                            mode='lines', 
                            name='Vertical'))
    fig.add_trace(go.Scatter(x=[min(spect['horizontal cycles [periods/pixel]'][0], 
                                    spect['vertical cycles [periods/pixel]'][0]), 
                                max(spect['horizontal cycles [periods/pixel]'][-1], 
                                    spect['vertical cycles [periods/pixel]'][-1])],
                            y=[param, param], 
                            mode='lines', 
                            name=paramstr, 
                            line=dict(dash='dot')))

    fig.update_yaxes(type="log")

    fig.update_layout(
                xaxis_title='Cycles [periods/pixel]',
                yaxis_title='Standard deviation and\nrelative presence of each cycle [DN]',
                title = f'Spectrogram {paramstr}')
    fig.show()


def image_with_rect(image, t_exp, mean_img, var_img, bpp, title='', rect_w=None, rect_h=None):
    '''Plot the image with a rectangle.

    Parameters
    ----------            
    image : np.array
        Image

    t_exp: float
        Exposure time when the image was taken
        
    mean_img : float
        Mean of the image

    var_img : float
        Variance of the image

    bpp : float
        Bits per pixel of the sensor

    title : str
        Head title

    rect_w : int
        Rectangle width

    rect_h : int
        Rectangle height
    '''
    fig = px.imshow(image, binary_string=True, 
                    title=f'{title} <br><sup>Exp [ms]: {t_exp/1e3:.2f}; avg [DN]: {mean_img:.2f}; var [DN]: {var_img:.2f}</sup>', 
                    labels={'x': 'Column', 'y':'Row'}, 
                    zmin=0, 
                    zmax=(1 << bpp) - 1)
    
    if (rect_w is not None) and (rect_h is not None):
        roi_grab_h = image.shape[0]
        roi_grab_w = image.shape[1]
        h = (roi_grab_h - rect_h)//2
        w = (roi_grab_w - rect_w)//2
        fig.add_shape(type="rect",
                    x0=w, y0=h, x1=roi_grab_w-w, y1=roi_grab_h-h,
                    line={"color":"RoyalBlue"})
    fig.show()